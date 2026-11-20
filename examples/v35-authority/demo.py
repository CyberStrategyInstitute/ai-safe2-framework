"""Run a synthetic approval, effect, duplicate retry and descendant stop."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json

from safe2.authority_fixture import AuthorityFixture, approve


def run():
    with TemporaryDirectory(prefix="safe2-v35-") as directory:
        key=b"synthetic-fixture-key-only-32-bytes"
        fixture=AuthorityFixture(Path(directory)/"fixture.sqlite",key)
        fixture.grant(principal="root",task="task",environment="test",resource="record",purpose="demo",ceiling=2,expires=1000)
        fixture.grant(principal="child",parent="root",task="task",environment="test",resource="record",purpose="demo",ceiling=2,expires=900)
        fixture.resource("record","initial")
        action={"key":"operation-1","principal":"child","task":"task","environment":"test","resource":"record","purpose":"demo","units":1,"expected_version":0,"value":"changed"}
        approval=approve(action,principal="child",expires=500,nonce="nonce",key=key)
        first=fixture.execute(action,approval,now=100)
        duplicate=fixture.execute(action,approval,now=100)
        fixture.revoke("root")
        stopped=fixture.execute(action,approval,now=100)
        assert first["effect"]=="BIND" and first==duplicate and stopped["effect"]=="NO_BIND"
        return {"first":first,"duplicate":duplicate,"after_stop":stopped,"scope":"local synthetic fixture"}


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
