import os
from pathlib import Path
from fastapi.testclient import TestClient

def test_workflow_and_stale_version(tmp_path, monkeypatch):
    monkeypatch.setenv("RELAY_DB_PATH",str(tmp_path/"test.db"))
    # Import/reload after setting the isolated database path.
    import importlib, app.main as main
    main.DB=Path(os.environ["RELAY_DB_PATH"]); main.init()
    client=TestClient(main.app); h={"Authorization":"Bearer tok-operator"}
    items=client.get("/api/items",headers=h).json()["items"]
    item=next(x for x in items if x["team"]=="Operations")
    claim=client.post(f"/api/items/{item['id']}/claim",headers={**h,"Idempotency-Key":"test-claim-1"})
    assert claim.status_code==200
    current=claim.json()
    good=client.patch(f"/api/items/{item['id']}",headers=h,json={"title":"Updated request","version":current["version"]})
    assert good.status_code==200
    stale=client.patch(f"/api/items/{item['id']}",headers=h,json={"title":"Lost update","version":current["version"]})
    assert stale.status_code==409

def test_viewer_cannot_claim(tmp_path, monkeypatch):
    monkeypatch.setenv("RELAY_DB_PATH",str(tmp_path/"viewer.db"))
    import app.main as main
    main.DB=Path(os.environ["RELAY_DB_PATH"]); main.init()
    c=TestClient(main.app); items=c.get("/api/items",headers={"Authorization":"Bearer tok-viewer"}).json()["items"]
    r=c.post(f"/api/items/{items[0]['id']}/claim",headers={"Authorization":"Bearer tok-viewer","Idempotency-Key":"viewer-1"})
    assert r.status_code==403

def test_approval_required_before_resolve(tmp_path, monkeypatch):
    monkeypatch.setenv("RELAY_DB_PATH",str(tmp_path/"approval.db"))
    import app.main as main
    main.DB=Path(os.environ["RELAY_DB_PATH"]); main.init()
    c=TestClient(main.app); h={"Authorization":"Bearer tok-analyst"}
    item=next(x for x in c.get("/api/items",headers=h).json()["items"] if x["approval_required"])
    r=c.post(f"/api/items/{item['id']}/transition",headers=h,json={"state":"resolved","version":item["version"]})
    assert r.status_code==403
