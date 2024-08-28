import asyncio
import csv
import datetime
import random

from sqlalchemy import select

from app.core.session import async_session


def generate_hex_code():
    """Generates a 28 digit hex code."""
    hex_code = ""
    for i in range(28):
        hex_code += random.choice("0123456789ABCDEF")
    return hex_code


# python -m app.initial_data
async def main() -> None:
    print("Start initial data")
    async with async_session() as session:
        # with open("products.csv", encoding="utf8") as csv_file:
        #     csv_reader = csv.DictReader(csv_file)
        #     machines = set()
        #     for row in csv_reader:
        #         machines.add(row["MACH_DESC"])
        # print(row["SEQ"])
        # session.add(
        #     Product(
        #         id=row["MATERIAL"],
        #         material_desc=row["MATERIAL_DESC"],
        #         maker_desc=row["MAKER_DESC"],
        #         part_no=row["PART_NO"],
        #     )
        # )
        #     machines = list(machines)
        # with open("products.csv", encoding="utf8") as csv_file:
        #     csv_reader = csv.DictReader(csv_file)
        #     for row in csv_reader:
        #         print("ok")
        #         session.add(
        #             Packet(
        #                 rfid=generate_hex_code(),
        #                 packet_type="new",
        #                 quantity=int(row["ROB"]),
        #                 product_id=row["MATERIAL"],
        #                 box_id=machines.index(row["MACH_DESC"]) + 1,
        #             )
        #         )
        # for index, machine in enumerate(machines):
        #     mac = Machine(id=index, machine_name=machine)
        #     session.add(mac)
        # for index, machine in enumerate(machines):
        #     session.add(
        #         Box(
        #             floor=random.randint(1, 3),
        #             room=random.randint(1, 3),
        #             rack=random.randint(1, 3),
        #             shelf=random.randint(1, 12),
        #             machine_id=index,
        #         )
        #     )
        # await session.commit()
        #     print(mac.id)
        #     # for machine in machines:
        #     #     # print(machine)
        #     session.add(Box(machine_name=machine))
        with open("pms.csv", encoding="utf8") as csv_file:
            csv_reader = csv.DictReader(csv_file)
            jobs = {}
            for index, row in enumerate(csv_reader):
                if jobs.get(row["pms_code"]) is None:
                    result = await session.execute(
                        select(Machine.id).where(Machine.machine_name == row["mach"])
                    )
                    result = result.scalar()
                    if result is None:
                        mac = Machine(machine_name=row["mach"])
                        session.add(mac)
                        await session.commit()
                        result = mac.id
                    jobs[row["pms_code"]] = {
                        "description": row["pms_desc"],
                        "due": datetime.datetime.now()
                        + datetime.timedelta(days=random.randint(1, 20)),
                        "status": "planning",
                        "interval": (
                            int(row["interval"]) * 730
                            if row["type"] == "CA"
                            else int(row["interval"])
                        ),
                        "machine_id": result,
                        "pic": random.randint(1, 3),
                        "products": [],
                    }
                    try:
                        session.add(
                            Job(
                                id=row["pms_code"],
                                description=row["pms_desc"],
                                due=datetime.datetime.now()
                                + datetime.timedelta(days=random.randint(1, 20)),
                                status="planning",
                                interval=(
                                    int(row["interval"]) * 730
                                    if row["type"] == "CA"
                                    else int(row["interval"])
                                ),
                                machine_id=result,
                                pic=random.randint(1, 3),
                            )
                        )
                        await session.commit()
                    except Exception as e:
                        print(e)

                if row["material_code"]:
                    jobs[row["pms_code"]]["products"].append(
                        (row["material_code"], int(row["WORK"]))
                    )
                    try:
                        session.add(
                            JobProduct(
                                job_id=row["pms_code"],
                                product_id=row["material_code"],
                                quantity=int(row["WORK"]),
                            )
                        )
                        await session.commit()
                    except Exception as e:
                        print(e)
                print(index)


if __name__ == "__main__":
    asyncio.run(main())
