"""Main FastAPI app instance declaration."""
import asyncio
import datetime
import json
import random
from typing import List

import emails
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import select, update

from app.api.api import api_router
from app.core import config
from app.core.session import async_session
from app.models import User, CampaignUser, Campaign
from app.utils.utils import generate_content


app = FastAPI(
    title=config.settings.PROJECT_NAME,
    version=config.settings.VERSION,
    description=config.settings.DESCRIPTION,
    openapi_url="/openapi.json",
    docs_url="/",
)
app.include_router(api_router)

# Sets all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in config.settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Guards against HTTP Host Header attacks
app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.settings.ALLOWED_HOSTS)


async def run_main():
    await asyncio.sleep(3)  # 5 Minutes sleep
    print("Running check")
    with open(
        f"app/email_templates/email_template{random.randint(1, 2)}.html", "r"
    ) as file:
        email_template = file.read()

    async with async_session() as session:
        campaigns_result = await session.execute(
            select(Campaign).where(
                (Campaign.campaign_timeline < datetime.datetime.now())
                & (Campaign.completed is False)
            )
        )

        campaigns: List[Campaign] = campaigns_result.scalars()

        # Iterate over the campaigns
        for campaign in campaigns:
            users_result = await session.execute(
                select(User, CampaignUser.unique_id)
                .join(CampaignUser, User.user_id == CampaignUser.user_id)
                .where(
                    (CampaignUser.campaign_id == campaign.campaign_id)
                    & (CampaignUser.sent.is_(None))
                )
            )
            users = users_result.fetchall()

            for user_result in users:
                print(user.name)
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
                    product_data=json.loads(json.loads(campaign.products)),
                    brand=campaign.company_name,
                    customer_name=user.name,
                    customer_age=user.age,
                    customer_gender=user.gender,
                    customer_industry=user.industry,
                    customer_company=user.company,
                    customer_tech_division=user.division,
                    email="company.email@example.com",
                    phone="+91 999-999-9999",
                    email_type="",
                    banner_url=f"https://email-marketing.naad.tech/track/open/{unique_id}",
                    product_view=f"https://email-marketing.naad.tech/track/link/{campaign.campaign_id}/{user.user_id}",
                    company_logo=company_logo,
                    other_details=json.loads(user.other_details),  # to be updated
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
                await session.execute(
                    update(CampaignUser)
                    .where(
                        (CampaignUser.user_id == user.user_id)
                        & (CampaignUser.campaign_id == campaign.campaign_id)
                    )
                    .values(sent="sent")
                )
                await session.commit()
            await session.execute(
                update(Campaign)
                .where(Campaign.campaign_id == campaign.campaign_id)
                .values(completed=True)
            )
            await session.commit()


@app.on_event("startup")
async def app_startup():
    await asyncio.create_task(run_main())
