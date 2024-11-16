import scrapy
import json
import os

class EdbsipderSpider(scrapy.Spider):
    name = "edbsipder"
    allowed_domains = ["esimdb.com"]

    start_urls = ["https://esimdb.com/api/client/countries?locale=en"]

    headers = {
        "Referer": "https://esimdb.com/",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }
    def start_requests(self):
        """
        Fetch the list of countries from the API
        """

        for url in self.start_urls:
            yield scrapy.Request(
                url,
                headers=self.headers,
                callback=self.parse_countries
            )


    def parse_countries(self, response):
        """
        Parse the list of countries from API
        """

        countries = json.loads(response.text)

        # loop through each country and fetch the respective country available data plans
        countries_new = []
        for country in countries:
            country_name = country.get('name')
            country_code = country.get('code')
            country_slug = country.get('slug')
            countries_new.append(country_slug)

            #Url to fetch country specific data plans
            plans_url =  f"https://esimdb.com/api/client/countries/{country_slug}/data-plans?locale=en"
            countries_new.append({
                'country': country_name,
                'url' : plans_url
            })
            yield scrapy.Request(
                url=plans_url,
                headers= self.headers,
                callback=self.parse_plans,
                meta={'name': country_name, 'code': country_code}
            )
        print("*******************************")
        print(f"{len(countries_new)} countries")
        print("*******************************")

    def parse_plans(self, response):
        """
        Parse eSim data plans for each countries
        """

        #access counry name and code from the meta dict
        country_name = response.meta['name']
        country_code = response.meta['code']
        

        # Parse the JSON response
        data = json.loads(response.text)

        providers = data.get('providers', {})

        plans = data.get('plans', [])

        country_data_plans = []

        for plan in plans:
            provider_id = plan.get('provider')
            provider_name = providers.get(provider_id, {}).get('name', 'Unknown Provider')
            plan_name = plan.get('name', 'N/A')
            plan_validity = f"{plan.get('period', 'N/A')} days"
            plan_price = plan.get('usdPrice', 0)
            capacity_gb = plan.get('capacity', 0)/1000
            price_per_gb = round(plan_price/capacity_gb, 2) if capacity_gb else '-'
            
            country_data_plans.append({
                'provider': provider_name,
                'plan': plan_name,
                'validity': plan_validity,
                'per_gb_price': price_per_gb,
                'capacity': capacity_gb,
                'price': plan_price
            })

            #save the data to respective JSON file
            # self.save(country_code=country_code, country_name=country_name, data = country_data_plans)


    def save(self, country_name,country_code, data):
        """
        Save the scraped data to JSON file named after the country name and code.
        """

        if not os.path.exists('output'):
            os.makedirs('output')

        filename = f'output/{country_code}_{country_name}.json'

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        self.log(f"Data scraped from the website")
        
    