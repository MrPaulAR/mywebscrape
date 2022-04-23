from datetime import datetime

from app import Sequence, Vendor, db
from sqlalchemy import and_


def delete_sequence(store, name, last_upd):
    vendor = Vendor.query.filter(Vendor.name == store).first()
    if vendor:
        looking_for_name = "%{0}%".format(name)

        vendorid = vendor.id
        row_cnt = Sequence.query.filter(
            and_(
                Sequence.vendor_id == vendorid,
                Sequence.name.ilike(looking_for_name),
                Sequence.time_updated < last_upd,
            )
        ).count()
        print(
            "Deleting %s rows from %s where name like %s and last_update is prior to %s"
            % (row_cnt, store, name, last_upd)
        )
        if row_cnt > 0:
            Sequence.query.filter(
                and_(
                    Sequence.vendor_id == vendorid,
                    Sequence.name.ilike(looking_for_name),
                    Sequence.time_updated < last_upd,
                )
            ).delete(synchronize_session="fetch")


def insert_sequence(store, url, name, price="-"):
    vendor = Vendor.query.filter(Vendor.name == store).first()
    sequence = Sequence(
        name=name,
        link=url,
        vendor_id=vendor.id,
        time_updated=datetime.now(),
        price=price,
    )
    print("Adding %s [%s]" % (sequence.name, price))
    seq = Sequence.query.filter(
        Sequence.link == url and Sequence.vendor_id == vendor.id
    ).first()
    if seq:
        Sequence.query.filter(
            Sequence.link == url and Sequence.vendor_id == vendor.id
        ).delete()
    else:
        seq = Sequence.query.filter(
            Sequence.name == name and Sequence.vendor_id == vendor.id
        ).first()
        Sequence.query.filter(
            Sequence.name == name and Sequence.vendor_id == vendor.id
        ).delete()
    if seq and seq.time_created:
        sequence.time_created = seq.time_created
    else:
        sequence.time_created = datetime.now()
    db.session.add(sequence)
    db.session.commit()


def create_or_update_product(sequences: list[Sequence]) -> None:
    for sequence in sequences:
        curr = Sequence.query.filter_by(link=sequence.link).first()
        if curr and sequence.price == curr.price:
            print(f"{sequence.name} already exists with price of {sequence.price}.")
        elif curr and sequence.price != curr.price:
            print(
                f"{sequence.name} price has changed from {sequence.price} to {curr.price}."
            )
            curr.price = sequence.price
        else:
            print(f"Adding {sequence.name} to database.")
            db.session.add(sequence)

        db.session.commit()
