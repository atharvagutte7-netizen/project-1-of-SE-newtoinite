"""Relay: small operations work queue demonstrating safe workflow mutations."""
import os, sqlite3, json
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT=Path(__file__).parent
DB=Path(os.getenv("RELAY_DB_PATH", str(ROOT.parent/"relay.db")))
app=FastAPI(title="Relay Operations Desk", version="1.0.0")
app.mount("/static", StaticFiles(directory=ROOT/"static"), name="static")
USERS={"tok-analyst":{"name":"Maya Chen","role":"analyst","team":"Payments"},"tok-operator":{"name":"Noah Williams","role":"operator","team":"Operations"},"tok-manager":{"name":"Priya Shah","role":"manager","team":"Management"},"tok-viewer":{"name":"Alex Morgan","role":"viewer","team":"Operations"}}

def now(): return datetime.now(timezone.utc).isoformat()
@contextmanager
def db():
    con=sqlite3.connect(DB, timeout=10); con.row_factory=sqlite3.Row
    try:
        con.execute("PRAGMA foreign_keys=ON"); yield con; con.commit()
    except: con.rollback(); raise
    finally: con.close()
def init():
    DB.parent.mkdir(parents=True,exist_ok=True)
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,description TEXT NOT NULL DEFAULT '',team TEXT NOT NULL,priority TEXT NOT NULL DEFAULT 'normal',state TEXT NOT NULL DEFAULT 'open',owner TEXT,approval_required INTEGER NOT NULL DEFAULT 0,approved_by TEXT,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS activity(id INTEGER PRIMARY KEY AUTOINCREMENT,item_id INTEGER NOT NULL,actor TEXT NOT NULL,action TEXT NOT NULL,detail TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(item_id) REFERENCES items(id));
        CREATE TABLE IF NOT EXISTS idempotency(key TEXT NOT NULL,actor TEXT NOT NULL,item_id INTEGER NOT NULL,PRIMARY KEY(key,actor));
        CREATE INDEX IF NOT EXISTS idx_items_team_state ON items(team,state,updated_at);
        """)
        if c.execute("SELECT count(*) FROM items").fetchone()[0]==0:
            seeds=[("Investigate duplicate settlement","Two settlement records appear for one payment batch.","Payments","high","open",1),("Review merchant onboarding","Confirm documents and risk notes before enabling the account.","Operations","normal","in_progress",0),("Reconcile daily report","Compare the dashboard total with the bank export.","Payments","low","open",0)]
            for title,desc,team,prio,state,approval in seeds:
                c.execute("INSERT INTO items(title,description,team,priority,state,approval_required,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",(title,desc,team,prio,state,approval,now(),now()))
                item=c.execute("SELECT last_insert_rowid()").fetchone()[0]
                c.execute("INSERT INTO activity(item_id,actor,action,detail,created_at) VALUES(?,?,?,?,?)",(item,"System","created","Seeded example request",now()))
init()
def user(authorization: str|None=Header(default=None)):
    token=(authorization or "").removeprefix("Bearer ").strip()
    if token not in USERS: raise HTTPException(401,"Use a demo bearer token.")
    return USERS[token]
def can_see(u,item):
    return u["role"]=="manager" or item["team"]==u["team"]
def row_item(r):
    d=dict(r); d["approval_required"]=bool(d["approval_required"]); return d
def get_item(c,item_id):
    r=c.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone()
    if not r: raise HTTPException(404,"Work item not found.")
    return r
def log(c,item_id,u,action,detail):
    c.execute("INSERT INTO activity(item_id,actor,action,detail,created_at) VALUES(?,?,?,?,?)",(item_id,u["name"],action,detail,now()))
class ItemCreate(BaseModel):
    title:str=Field(min_length=3,max_length=160)
    description:str=Field(default="",max_length=3000)
    team:str=Field(min_length=2,max_length=80)
    priority:str="normal"
    approval_required:bool=False
class ItemEdit(BaseModel):
    title:str|None=None
    description:str|None=None
    priority:str|None=None
    version:int
class Transition(BaseModel):
    state:str
    version:int
    reason:str=Field(default="",max_length=500)
class Approval(BaseModel):
    approved:bool
    reason:str=Field(min_length=3,max_length=500)
@app.get("/")
def home(): return FileResponse(ROOT/"static/index.html")
@app.get("/api/me")
def me(u=Depends(user)): return u
@app.get("/api/items")
def items(q:str="",state:str="",priority:str="",u=Depends(user),limit:int=50,offset:int=0):
    limit=max(1,min(limit,100)); offset=max(0,offset)
    sql="SELECT * FROM items WHERE (team=? OR ?='manager')"; args=[u["team"],u["role"]]
    if q: sql+=" AND (title LIKE ? OR description LIKE ?)"; args += [f"%{q}%",f"%{q}%"]
    if state: sql+=" AND state=?"; args.append(state)
    if priority: sql+=" AND priority=?"; args.append(priority)
    sql+=" ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END, updated_at DESC LIMIT ? OFFSET ?"; args += [limit,offset]
    with db() as c: return {"items":[row_item(r) for r in c.execute(sql,args)],"limit":limit,"offset":offset}
@app.post("/api/items",status_code=201)
def create(body:ItemCreate,u=Depends(user)):
    if u["role"]=="viewer": raise HTTPException(403,"Viewers cannot create work.")
    if u["role"]!="manager" and body.team!=u["team"]: raise HTTPException(403,"You can create work only for your team.")
    if body.priority not in ("low","normal","high"): raise HTTPException(422,"Invalid priority.")
    with db() as c:
        t=now(); cur=c.execute("INSERT INTO items(title,description,team,priority,approval_required,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",(body.title,body.description,body.team,body.priority,int(body.approval_required),t,t)); iid=cur.lastrowid
        log(c,iid,u,"created","Work item created")
        return row_item(get_item(c,iid))
@app.get("/api/items/{item_id}")
def detail(item_id:int,u=Depends(user)):
    with db() as c:
        r=get_item(c,item_id)
        if not can_see(u,r): raise HTTPException(403,"This item belongs to another team.")
        d=row_item(r); d["activity"]=[dict(a) for a in c.execute("SELECT actor,action,detail,created_at FROM activity WHERE item_id=? ORDER BY id DESC LIMIT 50",(item_id,))]
        return d
@app.patch("/api/items/{item_id}")
def edit(item_id:int,body:ItemEdit,u=Depends(user)):
    if u["role"]=="viewer": raise HTTPException(403,"Viewers cannot edit work.")
    with db() as c:
        r=get_item(c,item_id)
        if not can_see(u,r): raise HTTPException(403,"This item belongs to another team.")
        if r["version"]!=body.version: raise HTTPException(409,"This item changed. Reload and try again.")
        values={k:v for k,v in body.model_dump(exclude={"version"},exclude_none=True).items()}
        if not values: return row_item(r)
        if "priority" in values and values["priority"] not in ("low","normal","high"): raise HTTPException(422,"Invalid priority.")
        values.update(version=body.version+1,updated_at=now())
        c.execute("UPDATE items SET "+",".join(f"{k}=?" for k in values)+" WHERE id=? AND version=?",(*values.values(),item_id,body.version))
        if c.total_changes==0: raise HTTPException(409,"Concurrent update; reload.")
        log(c,item_id,u,"edited","Updated "+", ".join(k for k in values if k not in ("version","updated_at")))
        return row_item(get_item(c,item_id))
@app.post("/api/items/{item_id}/claim")
def claim(item_id:int,idempotency_key:str=Header(alias="Idempotency-Key"),u=Depends(user)):
    if u["role"]=="viewer": raise HTTPException(403,"Viewers cannot claim work.")
    with db() as c:
        r=get_item(c,item_id)
        if not can_see(u,r): raise HTTPException(403,"This item belongs to another team.")
        old=c.execute("SELECT item_id FROM idempotency WHERE key=? AND actor=?",(idempotency_key,u["name"])).fetchone()
        if old:
            if old["item_id"]!=item_id: raise HTTPException(409,"Idempotency key already used for another item.")
            return row_item(get_item(c,item_id))
        if r["owner"] and r["owner"]!=u["name"]: raise HTTPException(409,"Already claimed by another operator.")
        if r["state"] in ("resolved","cancelled"): raise HTTPException(409,"Closed work cannot be claimed.")
        cur=c.execute("UPDATE items SET owner=?,version=version+1,updated_at=? WHERE id=? AND version=? AND (owner IS NULL OR owner=?)",(u["name"],now(),item_id,r["version"],u["name"]))
        if cur.rowcount!=1: raise HTTPException(409,"Another user changed this item. Reload.")
        c.execute("INSERT INTO idempotency(key,actor,item_id) VALUES(?,?,?)",(idempotency_key,u["name"],item_id)); log(c,item_id,u,"claimed","Ownership assigned to "+u["name"])
        return row_item(get_item(c,item_id))
@app.post("/api/items/{item_id}/transition")
def transition(item_id:int,body:Transition,u=Depends(user)):
    allowed={"open":{"in_progress","cancelled"},"in_progress":{"open","resolved","cancelled"},"resolved":{"in_progress"},"cancelled":{"open"}}
    with db() as c:
        r=get_item(c,item_id)
        if not can_see(u,r): raise HTTPException(403,"This item belongs to another team.")
        if u["role"]=="viewer": raise HTTPException(403,"Viewers cannot change workflow state.")
        if r["version"]!=body.version: raise HTTPException(409,"Stale version; reload first.")
        if body.state not in allowed.get(r["state"],set()): raise HTTPException(422,f"Transition {r['state']} → {body.state} is not allowed.")
        if body.state=="resolved" and r["approval_required"] and not r["approved_by"]: raise HTTPException(403,"Independent approval is required before resolving.")
        c.execute("UPDATE items SET state=?,version=version+1,updated_at=? WHERE id=? AND version=?",(body.state,now(),item_id,body.version))
        log(c,item_id,u,"transition",f"{r['state']} → {body.state}"+(f": {body.reason}" if body.reason else ""))
        return row_item(get_item(c,item_id))
@app.post("/api/items/{item_id}/approval")
def approval(item_id:int,body:Approval,u=Depends(user)):
    if u["role"]!="manager": raise HTTPException(403,"Only a manager can approve requests.")
    with db() as c:
        r=get_item(c,item_id)
        if not r["approval_required"]: raise HTTPException(422,"This item does not require approval.")
        if r["owner"]==u["name"]: raise HTTPException(403,"The assignee cannot approve their own work.")
        c.execute("UPDATE items SET approved_by=?,state=?,version=version+1,updated_at=? WHERE id=?",(u["name"] if body.approved else None,"in_progress",now(),item_id))
        log(c,item_id,u,"approved" if body.approved else "rejected",body.reason)
        return row_item(get_item(c,item_id))
@app.get("/api/metrics")
def metrics(u=Depends(user)):
    with db() as c:
        rows=c.execute("SELECT state,count(*) n FROM items WHERE (team=? OR ?='manager') GROUP BY state",(u["team"],u["role"])).fetchall()
        return {r["state"]:r["n"] for r in rows}
