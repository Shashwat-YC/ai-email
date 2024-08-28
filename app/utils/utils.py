import os
from urllib.parse import urlparse

import emails
import google.generativeai as genai
import requests
from PIL import Image, ImageDraw, ImageFont

# import rembg
from bs4 import BeautifulSoup

import re
import json

genai.configure(api_key="AIzaSyC1xp0JCpkkWiNBJq_Fjfkw8Q3xSTh5i0E")
model = genai.GenerativeModel("gemini-pro")


def generate_content(
    product_data,
    brand,
    customer_name,
    customer_age,
    customer_gender,
    customer_industry,
    customer_company,
    customer_tech_division,
    email,
    phone,
    email_type,
    banner_url,
    product_view,
    company_logo,
    other_details,
):
    products_info = ", ".join(
        [
            f"{product['product_name']} at a special price of {product['product_price']}"
            for product in product_data
        ]
    )

    paragraph1_prompt = f"Discover the latest additions to our {brand} collection: {products_info}. Elevate your {brand} experience with these premium offerings. Remember not to directly mention customer information, but focus on selling the product based on the customer's characteristics."
    paragraph2_prompt = f"This exclusive offer is tailored for {customer_name}, a valued customer working in the {customer_industry} industry. With its innovative features and capabilities, our {brand} products are perfectly suited to enhance operations at {customer_company}'s {customer_tech_division} and these are few other details about the customer {other_details}. Remember not to directly mention customer information, but focus on selling the product based on the customer's characteristics."

    customer_age_int = int(customer_age)

    if customer_age_int < 30:
        age_group = "young"
    elif 30 <= customer_age_int < 60:
        age_group = "middle-aged"
    else:
        age_group = "senior"

    paragraph1_length = (
        "Write a concise paragraph with a minimum length of 150 words, focusing on the unique features and benefits of our products for the customer. This paragraph is for marketing purposes, so keep it informative yet concise."
        if email_type == "long"
        else "Write a concise paragraph with a maximum length of 50 words, highlighting the special price of our products. This paragraph is for marketing purposes, so keep it brief and enticing."
    )

    paragraph2_length = (
        f"Write a concise paragraph with a minimum length of 150 words, tailored for a {age_group} customer. Emphasize how our products cater to their needs in the {customer_industry} industry."
        if email_type == "long"
        else f"Write a concise paragraph with a maximum length of 50 words, addressing the customer directly and mentioning the relevance of our products to their industry. This paragraph is for marketing purposes, so keep it succinct."
    )

    paragraph1 = model.generate_content(
        f"You are an expert at generating paragraphs for marketing emails. {paragraph1_length}. Keeping that in mind, {paragraph1_prompt}"
    ).text
    paragraph2 = model.generate_content(
        f"You are an expert at generating paragraphs for marketing emails. {paragraph2_length}. Keeping that in mind, {paragraph2_prompt}"
    ).text

    footer = f"Thank you for choosing {brand}. For inquiries or assistance, reach out to our dedicated customer support team at {email} or call us at {phone}. We value your feedback and strive to provide the best service possible."

    heading = model.generate_content(
        f"Write a one line prompt for a marketing email for the following products - {products_info}. Make sure its snappy and only return the response and no other text"
    ).text

    return {
        "heading": heading,
        "paragraph1": paragraph1,
        "paragraph2": paragraph2,
        "footer": footer,
        "email": email,
        "phone": phone,
        "banner_link": banner_url,
        "product_view": product_view,
        "company_logo": company_logo,
    }


def extract_json(url):
    def extract_html(text):
        html_content = re.findall(r"<html[^>]*>(.*?)<\/html>", text, re.DOTALL)
        return html_content

    def get_html(urls):
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.5234.02 Safari/537.36"
        r = requests.get(url, headers={"User-Agent": user_agent})
        HTML = r.text
        html = extract_html(str(HTML))
        return html[-1]

    def extract_info(html):
        soup = BeautifulSoup(html, "html.parser")
        tags = soup.find_all(
            ["p", "a", "img", "span", "h1", "h2", "h3", "h4", "h5", "h6"]
        )
        html_simp = ""
        for i in tags:
            html_simp = html_simp + str(i)
        return html_simp

    def shorten_extracted_data(info):
        combined_data = []
        soup = BeautifulSoup(info, "html.parser")

        for link in soup.find_all(
            ["p", "a", "img", "span", "h1", "h2", "h3", "h4", "h5", "h6", "style"]
        ):
            try:
                url = link["href"]
                combined_data.append(url)
            except:
                pass
            try:
                url = link["src"]
                combined_data.append(url)
            except:
                pass
            try:
                text = link.get_text()
                combined_data.append(text)
            except:
                pass
        return combined_data

    def scraping(Question):
        reply = model.generate_content(
            f"""
          Given html content of a website, extract the details of product being sold on the website, you should extract, product name, price, image url and url

              "product_name"
              "product_price"
              "product_image_url"
              "product_url"

          in json format, display info of only first 5 products, the json should be complete

          {Question}
      """
        ).text
        return reply

    html = get_html(url)
    info = extract_info(html)
    combined_data = shorten_extracted_data(info)
    Data = scraping(str(combined_data))
    Data = Data.replace("\n", "")
    last_brace_index = Data.rfind("}")

    if "]" not in Data:
        Data = Data[: last_brace_index + 1] + "]"

    result = json.loads(Data)[::-1]

    for product in result:
        if url not in product["product_url"]:
            product["product_url"] = url + product["product_url"]
        else:
            pass

    return result


def download_image(image_url, img_filepath):
    if not os.path.exists(img_filepath):
        try:
            print(f"trying to download {image_url} -> {img_filepath}")
            response = requests.get(image_url)
            response.raise_for_status()
            with open(img_filepath, "wb") as f:
                f.write(response.content)
        except (requests.exceptions.RequestException, IOError) as e:
            print(f"Failed to download image: {e}")
            return False
    print(f"{img_filepath} already downloaded")
    return True


def generate_banner(campaign_id, products, brand):
    bg_img = Image.new("RGBA", (1600, 400), (255, 255, 255))  # #b8b8b8 background
    # "RBGA" instead of "RGB" did it (make sure the images are in the same mode while pasting)

    json_output = json.loads(products)
    json_output = json.loads(json_output)["products"]

    font = ImageFont.truetype(r"app/fonts/WorkSans-Italic-VariableFont_wght.ttf", 50)

    text = model.generate_content(
        f"based on this json data {json_output[:3]}, create a small slogan to be put on "
        f"a email banner - example(20% OFF\n on skateboards). Limit your response to 5-6 words only."
        f"Return only the slogan in your response and no other text."
    ).text

    draw = ImageDraw.Draw(bg_img)

    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

    text_x = 20
    text_y = (bg_img.height - text_height) // 2

    draw.text(
        (text_x, text_y), text=text, font=font, fill=(0, 0, 0)
    )  # Black text color

    product_spacing = 20
    total_product_height = 0

    for index, product in enumerate(json_output):
        image_url = product.get("product_image_url", "")
        if image_url and not image_url.startswith("https:"):
            image_url = "https:" + image_url

        img_filename = os.path.basename(urlparse(image_url).path)
        os.makedirs(f"app/images/{brand}", exist_ok=True)
        img_filepath = f"app/images/{brand}/{img_filename}"

        if not download_image(image_url, img_filepath):
            continue

    images_directory = f"app/images/{brand}"
    total_product_height = 0
    for index, image_filename in enumerate(os.listdir(images_directory)):
        img_filepath = os.path.join(images_directory, image_filename)

        try:
            # imgs = rembg.remove(Image.open(img_filepath))
            imgs = Image.open(img_filepath)
            rot_img1 = imgs.resize((imgs.width // 2 - 30, imgs.height // 2 - 30))
            # rot_img1 = remove_transparency(rot_img1)
            rot_img1 = rot_img1.convert(
                "RGBA"
            )  # this did it (make sure the images are in the same mode while pasting)

            product_x = bg_img.width - rot_img1.width - 20
            # print(f"product_x -> {img_filepath}: {product_x}")
            product_y = total_product_height  # Update product_y calculation
            # print(f"product_x -> {img_filepath}: {product_y}")
            total_product_height += rot_img1.height + 20  # Update total_product_height
            # print(f"total_product_height -> {img_filepath}: {total_product_height}")

            bg_img.paste(rot_img1, (product_x, product_y), rot_img1)
            print(f"{rot_img1} pasted!")

            break

        except Exception as e:
            print(f"Failed to process image: {e}")

    # logo = rembg.remove(Image.open(f"app/images/logos/{brand}.png"))
    logo = Image.open(f"app/images/logos/{brand}.png")
    logo_width, logo_height = logo.size
    aspect_ratio = logo_height / logo_width

    if aspect_ratio > 1:
        new_logo_height = 125
        new_logo_width = round(125 / aspect_ratio)
    else:
        new_logo_width = 125
        new_logo_height = round(125 * aspect_ratio)

    logo = logo.resize((new_logo_width, new_logo_height))
    bg_img.paste(logo, (20, 20))

    bg_img.save(f"app/images/banners/{campaign_id}.png", format="png")
    print(f"final banner for campaign {campaign_id} pasted")

    return f"app/images/banners/{campaign_id}.png"


# if __name__ == "__main__":
#     a = extract_json("https://www.urbanmonkey.com/collections/skate")
#     print(a)
