import datetime
import json
import time
from io import BytesIO
import random

import emails
import pandas
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends,
    BackgroundTasks,
    Form,
)
from sqlalchemy import select, func, distinct, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.api import deps
from app.api.email_type import EmailType
from app.core.session import async_session
from app.models import Campaign, CampaignUser, OpenLog, LinkLog, User
from app.schemas.requests import Products, CampaignCreate
from app.utils.segmentation import *
from app.utils.utils import generate_content, generate_banner, extract_json

api_router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def create_banner(campaign: Campaign):
    generate_banner(
        campaign.campaign_id, campaign.products, str(campaign.company_name).lower()
    )


async def send_email_rest(campaign: Campaign, email_type: str):
    with open(
        f"app/email_templates/email_template{random.randint(1, 2)}.html", "r"
    ) as file:
        email_template = file.read()

    async with async_session() as session:
        users_result = await session.execute(
            select(User, CampaignUser.unique_id)
            .join(CampaignUser, User.user_id == CampaignUser.user_id)
            .where(
                (CampaignUser.campaign_id == campaign.campaign_id)
                & (CampaignUser.sent.is_(None))
            )
        )
        users = users_result.fetchall()

        products = json.loads(campaign.products)
        products = json.loads(products)["products"]

        for user_result in users:
            user: User = user_result[0]
            unique_id: int = user_result[1]
            print(user.name, unique_id)
            if "google" in user.company:
                company_logo = (
                    "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_%22G%22_logo.svg"
                    "/1024px-Google_%22G%22_logo.svg.png"
                )
            if "apple" in user.company:
                company_logo = "https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg"
            else:
                company_logo = (
                    "https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Samsung_Logo.svg/2560px"
                    "-Samsung_Logo.svg.png"
                )
            dynamic_content = generate_content(
                product_data=products,
                brand=campaign.company_name,
                customer_name=user.name,
                customer_age=user.age,
                customer_gender=user.gender,
                customer_industry=user.industry,
                customer_company=user.company,
                customer_tech_division=user.division,
                email=user.email,
                phone="+91 999-999-9999",
                email_type=email_type,
                banner_url=f"https://email-marketing.naad.tech/track/open/{unique_id}",
                product_view=f"https://email-marketing.naad.tech/track/link/{campaign.campaign_id}/{user.user_id}",
                company_logo=company_logo,
                other_details=json.loads(users_result.other_details),  # to be updated
            )
            email_content = email_template.format(**dynamic_content)

            message = emails.html(
                html=email_content,
                subject=f"Final Email for {user.name}",
                mail_from="rohan@consti.rohan.gg",
            )

            result = message.send(
                to=user.email,
                smtp={
                    "host": "smtp.resend.com",
                    "port": 465,
                    "ssl": True,
                    "user": "resend",
                    "password": "re_VwvxTUmr_5BLdjPvt5K7ywBW2dga4Ziwx",
                },
            )


async def send_email(contacts: pandas.DataFrame, campaign: Campaign):
    print("sending emails to experimental group")
    with open(
        f"app/email_templates/email_template{random.randint(1, 2)}.html", "r"
    ) as file:
        email_template = file.read()
    length = len(contacts)
    async with async_session() as session:
        products = json.loads(campaign.products)
        products = json.loads(products)["products"]

        await session.execute(
            delete(OpenLog).where(
                OpenLog.campaign_user_id.in_(
                    select(CampaignUser.unique_id).where(
                        CampaignUser.campaign_id == campaign.campaign_id
                    )
                )
            )
        )

        await session.execute(
            delete(LinkLog).where(LinkLog.campaign_id == campaign.campaign_id)
        )

        await session.execute(
            delete(CampaignUser).where(CampaignUser.campaign_id == campaign.campaign_id)
        )
        await session.commit()
        for index, row in contacts.iterrows():

            print(row)
            user_r = await session.execute(
                select(User).where(
                    (User.name == row["Name"])
                    & (User.email == row["Email"])
                    & (User.age == str(row["Age"]))
                    & (User.gender == row["Gender"])
                    & (User.industry == row["Industry"])
                    & (User.company == row["Company"])
                    & (User.division == row["Division"])
                )
            )

            excluded_fields = [
                "Name",
                "Email",
                "Age",
                "Gender",
                "Industry",
                "Company",
                "Division",
            ]
            other_details = {
                key: value for key, value in row.items() if key not in excluded_fields
            }

            user: User = user_r.scalars().first()
            if user is None:
                user: User = User(
                    name=row["Name"],
                    email=row["Email"],
                    age=str(row["Age"]),
                    gender=row["Gender"],
                    industry=row["Industry"],
                    company=row["Company"],
                    division=row["Division"],
                    other_details=json.dumps(other_details),
                )
                session.add(user)
                await session.commit()
            if "google" in user.company:
                company_logo = (
                    "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_%22G%22_logo.svg"
                    "/1024px-Google_%22G%22_logo.svg.png"
                )
            if "apple" in user.company:
                company_logo = "https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg"
            else:
                company_logo = (
                    "https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Samsung_Logo.svg/2560px"
                    "-Samsung_Logo.svg.png"
                )
            if index <= length//4:
                campaign_user = CampaignUser(
                    user_id=user.user_id, campaign_id=campaign.campaign_id, sent="long"
                )
                session.add(campaign_user)
                await session.commit()

                dynamic_content = generate_content(
                    product_data=products,
                    brand=campaign.company_name,
                    customer_name=user.name,
                    customer_age=user.age,
                    customer_gender=user.gender,
                    customer_industry=user.industry,
                    customer_company="Google",
                    customer_tech_division="Software Engineering",
                    email="company.email@example.com",
                    phone="+91 999-999-9999",
                    email_type="long",
                    banner_url=f"https://email-marketing.naad.tech/track/open/{campaign_user.unique_id}",
                    product_view=f"https://email-marketing.naad.tech/track/link/{campaign.campaign_id}/{user.user_id}",
                    company_logo=company_logo,
                    other_details=other_details,
                )
                email_content = email_template.format(**dynamic_content)
                message = emails.html(
                    html=email_content,
                    subject=f"Lengthy Mail Type (Experimental Group) for {user.name}",
                    mail_from="rohan@consti.rohan.gg",
                )

                result = message.send(
                    to=user.email,
                    smtp={
                        "host": "smtp.resend.com",
                        "port": 465,
                        "ssl": True,
                        "user": "resend",
                        "password": "re_VwvxTUmr_5BLdjPvt5K7ywBW2dga4Ziwx",
                    },
                )
            elif index <= length//2:
                campaign_user = CampaignUser(
                    user_id=user.user_id, campaign_id=campaign.campaign_id, sent="short"
                )

                session.add(campaign_user)
                await session.commit()
                dynamic_content = generate_content(
                    product_data=products,
                    brand=campaign.company_name,
                    customer_name=user.name,
                    customer_age=user.age,
                    customer_gender=user.gender,
                    customer_industry=user.industry,
                    customer_company=user.company,
                    customer_tech_division=user.division,
                    email="company.email@example.com",
                    phone="+91 999-999-9999",
                    email_type="short",
                    banner_url=f"https://email-marketing.naad.tech/track/open/{campaign_user.unique_id}",
                    product_view=f"https://email-marketing.naad.tech/track/link/{campaign.campaign_id}/{user.user_id}",
                    company_logo=company_logo,
                    other_details=other_details,
                )
                email_content = email_template.format(**dynamic_content)
                message = emails.html(
                    html=email_content,
                    subject=f"Short Mail Type (Experimental Group) for {user.name}",
                    mail_from="rohan@consti.rohan.gg",
                )

                result = message.send(
                    to=user.email,
                    smtp={
                        "host": "smtp.resend.com",
                        "port": 465,
                        "ssl": True,
                        "user": "resend",
                        "password": "re_VwvxTUmr_5BLdjPvt5K7ywBW2dga4Ziwx",
                    },
                )
            else:
                campaign_user = CampaignUser(
                    user_id=user.user_id, campaign_id=campaign.campaign_id, sent=None
                )

                session.add(campaign_user)
                await session.commit()


@api_router.get("/fake_timing")
async def email_send_all(
    background_tasks: BackgroundTasks,
    campaign_id: int,
    long: bool,
    session: AsyncSession = Depends(deps.get_session),
):
    campaign_r = await session.execute(
        select(Campaign).where(Campaign.campaign_id == campaign_id)
    )
    campaign: Campaign = campaign_r.scalars().first()
    background_tasks.add_task(send_email_rest, campaign, long)


@api_router.get("/email_tracking_test_email_send")
async def email_tracking_test_email_send(
    session: AsyncSession = Depends(deps.get_session),
):
    message = emails.html(
        html="""<img src="https://email-marketing.naad.tech/track/open/1" alt="Open Tracking Pixel">""",
        subject="Test",
        mail_from="rohan@consti.rohan.gg",
    )

    result = message.send(
        to="naadkd@gmail.com",
        smtp={
            "host": "smtp.resend.com",
            "port": 465,
            "ssl": True,
            "user": "resend",
            "password": "re_VwvxTUmr_5BLdjPvt5K7ywBW2dga4Ziwx",
        },
    )
    return 200


@api_router.post("/create_campaign")
async def create_campaign(
    background_tasks: BackgroundTasks,
    campaign_create: CampaignCreate,
    session: AsyncSession = Depends(deps.get_session),
):
    campaign = Campaign(
        campaign_threshold=campaign_create.threshold,
        company_name=campaign_create.company_name,
        company_url=campaign_create.company_url,
        products=json.dumps(
            campaign_create.model_dump_json(
                include={
                    "products",
                }
            )
        ),
        campaign_timeline=datetime.datetime.now(),
        completed=False,
    )
    session.add(campaign)
    await session.commit()
    background_tasks.add_task(create_banner, campaign)
    return {"campaign_id": campaign.campaign_id}


@api_router.post("/load_csv")
async def load_csv(
    background_tasks: BackgroundTasks,
    campaign_id: int = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(deps.get_session),
):
    if not file.filename.endswith(".csv"):
        return HTTPException(detail="Please upload csv files only", status_code=500)
    contents = await file.read()
    df = pandas.read_csv(BytesIO(contents))

    result = await session.execute(
        select(Campaign).where(Campaign.campaign_id == campaign_id)
    )

    campaign: Campaign = result.scalars().first()
    background_tasks.add_task(send_email, df, campaign)


@api_router.get("/track/open/{campaign_user_id}")
async def track_open(
    background_tasks: BackgroundTasks,
    campaign_user_id: int,
    session: AsyncSession = Depends(deps.get_session),
):
    # result = await session.execute(
    #     select(CampaignUser).where(CampaignUser.unique_id == campaign_user_id)
    # )
    # row: CampaignUser = result.scalars().first()
    # print(row.campaign_id)
    # print(row.unique_id)
    # print(row.user_id)
    result = await session.execute(
        select(
            CampaignUser,
            Campaign.campaign_threshold,
            Campaign.campaign_id,
            Campaign.completed,
        )
        .join(Campaign, Campaign.campaign_id == CampaignUser.campaign_id)
        .where(CampaignUser.unique_id == campaign_user_id)
    )

    if result:
        row = result.fetchone()
        campaign_user: CampaignUser = row[0]
        threshold: int = row[1]
        campaign_id: int = row[2]
        completed: bool = row[3]
        print(campaign_id)
        session.add(
            OpenLog(
                open_time=datetime.datetime.now(),
                campaign_user_id=campaign_user.unique_id,
            )
        )
        await session.commit()
        if completed is False:
            result = await session.execute(
                select(func.count(distinct(OpenLog.campaign_user_id)))
                .join(CampaignUser)
                .where(CampaignUser.campaign_id == campaign_id)
                .where(CampaignUser.sent == campaign_user.sent)
            )
            count = result.scalar_one()
            if count >= threshold:
                campaign = await session.get(Campaign, campaign_id)
                if campaign is None:
                    raise HTTPException(status_code=404, detail="Campaign not found")
                campaign.completed = True
                background_tasks.add_task(
                    send_email_rest,
                    campaign,
                    True if campaign_user.sent == "long" else False,
                )
                await session.commit()

        with open(f"app/images/banners/{campaign_id}.png", "rb") as image_file:
            image_data = image_file.read()

        # Return the image as a StreamingResponse
        return StreamingResponse(BytesIO(image_data), media_type="image/png")


@api_router.get("/track/link/{campaign_id}/{user_id}", response_class=RedirectResponse)
async def track_link(
    campaign_id: int, user_id: int, session: AsyncSession = Depends(deps.get_session)
):
    try:
        link = await session.execute(
            select(Campaign.company_url).where(Campaign.campaign_id == campaign_id)
        )
        link = link.scalar_one()
        link_log = LinkLog(
            click_time=datetime.datetime.now(), campaign_id=campaign_id, user_id=user_id
        )
        session.add(link_log)
        await session.commit()
        return RedirectResponse(url=link)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# @api_router.post("/create_campaign_from_csv")
# async def create_campaign_from_csv(
#     campaign: CampaignCreate,
#     file: UploadFile = File(...),
#     session: AsyncSession = Depends(deps.get_session),
# ):
#     if not file.filename.endswith(".csv"):
#         raise HTTPException(detail="Please upload csv files only", status_code=400)
#
#     contents = await file.read()
#     df = pd.read_csv(BytesIO(contents))
#
#     new_campaign = Campaign(
#         campaign_threshold=3,
#         company_name=campaign.name,
#         company_url=campaign.url,
#         products=json.dumps(campaign.products),
#         completed=False,
#     )
#     session.add(new_campaign)
#
#     num_segments = 12
#     num_subgroups_per_segment = 5
#     contacts_per_subgroup = 10
#     segments = [[] for _ in range(num_segments)]
#
#     index_mapping = {
#         field: map_values_to_index(set(df[field]))
#         for field in ["Age", "Gender", "Industry"]
#     }
#
#     # entries into segments
#     for _, row in df.iterrows():
#         segment_index = calculate_segment_index(row, index_mapping)
#         segments[segment_index].append(row)
#
#     # Save contacts for each segment and subgroup
#     create_subgroups(segments, num_subgroups_per_segment, contacts_per_subgroup)
#
# for _, row in df.iterrows():
#     user = User(
#         name=row["Name"],
#         email=row["Email"],
#         age=row["Age"],
#         gender=row["Gender"],
#         industry=row["Industry"],
#     )
#     session.add(user)
#
#     campaign_user = CampaignUser(
#         user_id=user.user_id,
#         campaign_id=new_campaign.campaign_id,
#         sent=None,
#     )
#     session.add(campaign_user)
#
# await session.commit()
#
# return {"message": "Campaign created successfully"}


@api_router.get("/scan_url")
async def get_scan_url(url: str):
    try:
        result = extract_json(url)
        return {"products": result}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="An error occurred while processing the request"
        )


@api_router.get("/dashboard")
async def dashboard(
    request: Request, session: AsyncSession = Depends(deps.get_session)
):
    campaigns = []

    # Retrieve all campaigns
    result = await session.execute(select(Campaign))
    for campaign in result.scalars():
        long_opens = await get_opens_count(session, campaign.campaign_id, sent="long")
        short_opens = await get_opens_count(session, campaign.campaign_id, sent="short")

        status = "Completed" if campaign.completed else "Ongoing"

        campaigns.append(
            {
                "campaign_id": campaign.campaign_id,
                "long_opens": long_opens,
                "short_opens": short_opens,
                "none_opened": "False" if long_opens > 0 and short_opens else "True",
                "status": status,
            }
        )

    return templates.TemplateResponse(
        "campaigns.html", {"request": request, "campaigns": campaigns}
    )


async def get_opens_count(session, campaign_id, sent):
    result = await session.execute(
        select(func.count(OpenLog.open_id))
        .join(CampaignUser, OpenLog.campaign_user_id == CampaignUser.unique_id)
        .filter(CampaignUser.campaign_id == campaign_id)
        .filter(CampaignUser.sent == sent)
    )
    return result.scalar()


@api_router.get("/campaign/{campaign_id}/links")
async def campaign_links(
    campaign_id: int,
    request: Request,
    session: AsyncSession = Depends(deps.get_session),
):
    links = []

    result = await session.execute(
        select(LinkLog, User)
        .join(
            CampaignUser,
            and_(
                CampaignUser.campaign_id == LinkLog.campaign_id,
                CampaignUser.user_id == LinkLog.user_id,
            ),
        )
        .join(User, User.user_id == CampaignUser.user_id)
        .filter(CampaignUser.campaign_id == campaign_id)
    )
    for link, user in result:
        links.append(
            {
                "link_id": link.click_id,
                "email": user.email,
                "click_time": link.click_time,
            }
        )

    return templates.TemplateResponse(
        "campaign_links.html",
        {"request": request, "campaign_id": campaign_id, "links": links},
    )
