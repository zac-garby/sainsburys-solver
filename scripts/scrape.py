import os
import re
import json
import requests
import shutil

from typing import Dict
from pathlib import Path

product_url = "https://www.sainsburys.co.uk/groceries-api/gol-services/product/v1/product"
headers = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "enabled-feature-flags": "add_to_favourites,occasions,use_food_basket_service,use_food_basket_service_v3,ads_conditionals,findability_v5,show_static_cnc_messaging,fetch_future_slot_weeks,click_and_collect_promo_banner,cookie_law_link,citrus_banners,citrus_favourites_trio_banners,offers_trio_banners_single_call,special_logo,custom_product_messaging,promotional_link,findability_search,findability_autosuggest,findability_orchestrator,fto_header_flag,recurring_slot_skip_opt_out,first_favourite_oauth_entry_point,seasonal_favourites,cnc_start_amend_order_modal,favourites_product_cta_alt,get_favourites_from_v2,offers_config,alternatives_modal,relevancy_rank,changes_to_trolley,nectar_destination_page,nectar_card_associated,meal_deal_live,browse_pills_nav_type,zone_featured,use_cached_findability_results,event_zone_list,cms_carousel_zone_list,show_ynp_change_slot_banner,recipe_scrapbooks_enabled,event_carousel_skus,trolley_nectar_card,golui_payment_cards,favourites_magnolia,homepage,taggstar,meal_deal_cms_template_ids,frequently_bought_together,food_to_order_trial_modal,pdp_meta_desc_template,grouped_meal_deals,new_filters,meganav,enable_favourites_priority,xmas_slot_guide_enabled,occasions_navigation,slots_event_banner_config,rokt,sales_window,resting_search,taggstar_config,all_ad_components_enabled,call_bcs,catchweight_dropdown,citrus_preview_new,citrus_search_trio_banners,citrus_xsell,compare_seasonal_favourites,constant_commerce_v2,desktop_interstitial_variant,disable_product_cache_validation,event_dates,favourites_pill_nav,favourites_whole_service,first_favourites_static,foodmaestro_modal,hfss_restricted,interstitial_variant,kg_price_label,krang_recommendations,meal_planner,mobile_interstitial_variant,nectar_prices,new_favourites_service,ni_brexit_banner,promo_lister_page,recipes_ingredients_modal,review_syndication,sale_january,show_hd_xmas_slots_banner,similar_products,sponsored_featured_tiles,xmas_dummy_skus,your_nectar_prices",
    "Cookie": "JSESSIONID=0000stOPbQ407lV-b5_bVXMr49D:1hj7e34pe; _abck=E7C3BCAD4E41B4A3D5EA60ED64104EA6~-1~YAAQUpp6XOx9VwaTAQAA4KukHwwY1Ojy+RTJj/L8nuu1KW4jJl9W8MoS0l/8ZKMyMdS9qqyTFyEYb8uULFZezv3zLsWd6wcvgBwZIuTq/YOY7GUJUWFNB6HW16R8VY2PYHHIof2aj7KaHyET5sXLrSMPL1K71aeQ1OWB0Q0Pt+mBiFr4rLDccUxq10fWsSi+t4Y8jVoz9kmssSHTVAyDQ/iKJPDLR0//+sagbnYvEDhFjDnJMkglF3p0FC/pdPV6CSAwOpe6sCo09QnajvrWRLwu4dKufYgzRi6xu8Ox9ZGAX809Phdkdfgp5Jgh/Rp/sOuv6OSz33NOSGYSj1vYYI2OkRvci42sDzvLTjSL5P9/1qloFJkWPefr9zsOQttbHXt6g28RiTjtmnaW3itJpGf1kHxXJvveDjV3YorvK7hEvubifxCKIpBJ/BVTx+xi7AfdaqtmnQrUqRcMrzs7RqNVh1iyezOCTRD2V+5FNKSwK51NIYaHJYwUt3ZUQCyvogW6ACD7DgtOdOwVjULD4JxOfIWuAfDuPWsKwhNVAnyd4BM=~0~-1~-1; Apache=10.8.240.7.1731402713658678; ak_bmsc=EB0D5ACB69F70971094B547979A55141~000000000000000000000000000000~YAAQUpp6XOh+VwaTAQAAKeukHxm8EcnbPEtJH4ooOkCLYO2MO9E7Z609NyvWaXpk7XcBRCj7RA+qxJc0r3KmtN+V2eNoDqD/fES0trVJZPE8wgGcFVWXT6qWs2lxKLYQgzZmC8hIoZe7JVUYTxTtFAMgLulEYi3saFl0R16IlmnwgteqDKB0U7ypk7X7wPk9Dme2YE+cyWP3pHorR6kC92mkpVbrk8RmI2m+1gz/exOotmQWKmr84cUFxJ2poUDcodRd7HU+P0zGmGQ3GQ7MrDpLMkEg9kYgF0Y9lwP/qreZ7x2ncLopcZbrPDZBQyQW93DvOt3MzR76f0z6KEMKuSZ9Hi6OIcOlqI6BKu6zHQw9OJB2ZoNvl+6tOUQWoAcR; WC_PERSISTENT=BhrRURC1HY5E2%2F5DpGLlp7g9NFM%3D%0A%3B2024-11-12+09%3A13%3A07.688_1731402787688-4830_0; bm_sz=24516C5CC60F3165B07A8D2FB7A95603~YAAQUpp6XLWdVwaTAQAAmy2sHxl0A6mrmG6KG234C4FNDVGcLt7AYzK6UuuqQYhkSRZZTQM4DNMmoZIIlMiYLMaZsc/dUIC/G+OuIa8JaaqVx7TK0YxUllKtA6DG6xh+VQbGEwyuuvlstBIIpKYHVrRLPLy6jetGq6FYGCQO0YsRvuPStm3ggjp8a30Pmn3ACcq34TyDgJGTlRK/uLSlwkrTwYDuot66ttKBU7k7eozSNku/K11pliSaVP6Vxwf4fRcaqUUDO42rS1s/bN61xLnV51r6haLkjP9rTdv5lH/IGlCEUsnjxu9y+lzV7Jh0auKUR71SDsUhimTp5OeA6rhPP4p+xdnSgz0z0TNTC6F8aZtSaUDyvKuNIh6bnPQxR4uYWqYwpmuRcak/1B2JK2zVULQwbtScdrCqP678Cq1xhVrradSNHfsBigZ/EYKjCFCpjVKTLiy0qtj2Pq54w2bfzkKv3ZpBpiMThQQ+Iix9jlvl4mTHOfZD9iJ7qRPGHGcoYamU781t+HeP5p6iZFNIQvnar2s6vtE9kuTt9dH5aOzzI8UmM+K0sw==~3425075~3420208; AWSALB=/bBR5boS6yz2ZLJstYxtU/3eLi7cohXJ1q6YYZJhxuKrEsMrxp2aNw6zmLXMCL5esDZ1s3ep3VGgRDUgWbgIOrS0Cw9DMZogJW9oBxNFY3uejidEwrcKtyTSxNd3; AWSALBCORS=/bBR5boS6yz2ZLJstYxtU/3eLi7cohXJ1q6YYZJhxuKrEsMrxp2aNw6zmLXMCL5esDZ1s3ep3VGgRDUgWbgIOrS0Cw9DMZogJW9oBxNFY3uejidEwrcKtyTSxNd3; akavpau_vpc_gol_default=1731404026~id=f8c0a022dc65b697c995041503277b12; bm_sv=52727300060D41FEE5EBD37295C31B5F~YAAQSpp6XOPnbe6SAQAAtj60HxkSuSBMpkYkjXe04HXt6jljUY/YTR6+x/965hPItim4sexcYCAjSoqunEcyhjuE+BNqv2c3iBIvT4WfZkcUlGmGty8mqbeQkgZTT6QX/C7i2W/Q1/arP73KkHm5JyKM5AuW8QL2VHb7iCOaaZbo33F5+TXa22JHNIjnXBARRQjoNnc7v+i5WiZIWh0PY5zsJrP4LRpUh6hwemBsOIvLHnjuHPCct/S4DJrBra+44ORs1yK1TA==~1"
}

ignore_categories = [
    # 1018771,
    # 1019012,
    # 1020225,
    # 1020324,
    # 1045274,
    # 1043776,
    # 1043379,
    # 1044170,
    # 1043310,
    # 1020464,
    # 1045745,
    # 1020827,
    # 1044114,
    # 1046171,
]

scraped_ids: Dict[int, Path] = {}

def main():
    with open('data/taxonomy.json') as f:
        taxonomy = json.load(f)["data"]
        for top_level in taxonomy:
            find_all(top_level)

def find_all(category, prior = []):
    name = category["name"]
    id = category["id"]
    children = category["children"]
    new_prior = prior + [name]

    if id in ignore_categories:
        return

    print(" > ".join(new_prior))
    path = Path("data/out").joinpath(*(filename_safe(p) for p in new_prior))
    path.mkdir(parents=True, exist_ok=True)

    if len(children) > 0:
        for child in children:
            find_all(child, new_prior)
    else:
        scrape_category(id, path)

def scrape_category(id, path):
    print(f"  scraping category {id} into {path}")

    params={
        "filter[keyword]": "",
        "filter[category]": id,
        "browse": "true",
        "hfss_restricted": "false",
        "page_size": 1000,
    }

    try:
        response = requests.get(
            url=product_url,
            params=params,
            headers=headers,
        )

        if response.status_code == 200:
            data = response.json()
            products = data["products"]
            controls = data["controls"]

            if controls["total_record_count"] > controls["returned_record_count"]:
                print(f"  ? ignoring extra items. just using {controls['returned_record_count']}/{controls['total_record_count']}")

            for product in products:
                scrape_item(product, path)
        else:
            print("  ! got a non-200 response")
    except requests.exceptions.RequestException:
        print("  ! http request failed")

def scrape_item(product, path: Path):
    name = product["name"]
    id = product["product_uid"]
    filepath = path.joinpath(f"{id}.json")

    if id in scraped_ids:
        if not filepath.exists():
            print(f"    copying product {id} as it's already been scraped in another category")
            shutil.copy2(scraped_ids[id], filepath)
        else:
            print(f"    product {id} already scraped and already there; skipping")

        return

    if filepath.exists():
        print(f"    skipping product {id} as it's already there")
        scraped_ids[id] = filepath
        return

    path_stem = Path(product["full_url"]).stem
    print(f"    scraping product {id}: {name}")

    params={
        "filter[product_seo_url]": path_stem,
    }

    try:
        response = requests.get(
            url=product_url,
            params=params,
            headers=headers,
        )

        if response.status_code == 200:
            data = response.json()

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
                scraped_ids[id] = filepath
                print(f"      written to {filepath}")
        else:
            print("  ! got a non-200 response")
    except requests.exceptions.RequestException:
        print("  ! http request failed")

def filename_safe(string: str) -> str:
    string = string.replace("&", "and").replace(",", "")
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', string).lower()

if __name__ == "__main__":
    main()
