from sqlmodel import Session
from db import engine, init_db
from models import User, ScanRecord
from auth import get_password_hash


def seed():
    init_db()
    with Session(engine) as session:
        # create default user
        existing = session.query(User).filter(User.username == "admin").first()
        if not existing:
            user = User(username="admin", full_name="Administrator", hashed_password=get_password_hash("password"))
            session.add(user)

        # sample records
        sample_ids = [f"PT-2025-00{i}" for i in range(1, 9)]
        for i, pid in enumerate(sample_ids, start=1):
            rec = session.query(ScanRecord).filter(ScanRecord.patient_id == pid).first()
            if not rec:
                r = ScanRecord(patient_id=pid, view_type="PA" if i % 3 != 0 else "Lateral", device="GE Discovery XR656" if i % 2 == 0 else "Philips DigitalDiagnost", qc_status="PASS")
                session.add(r)

        session.commit()


if __name__ == '__main__':
    seed()
