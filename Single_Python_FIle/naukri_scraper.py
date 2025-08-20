import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import time
import re
import os

def initialize_driver():
    """Initializes and returns a Chrome WebDriver."""
    driver = webdriver.Chrome()
    driver.maximize_window()
    return driver

# ----------- CONFIGURATION -------------
job_role = "SDET"       # Enter Role here.
num_pages = 1  # Change number of pages to be scrapped here.
# ---------------------------------------

# Get current script directory
script_dir = os.path.dirname(os.path.abspath(__file__))



def scrape_naukri_jobs(driver, num_pages):
    """
    Scrapes job data from Naukri.com for a specified number of pages.

    Args:
        driver: The Selenium WebDriver instance.
        num_pages (int): The number of pages to scrape.

    Returns:
        dict: A dictionary containing scraped job data.
    """
    jobs = {
        "job_no": [],
        "roles": [],
        "companies": [],
        "locations": [],
        "experience": [],
        "salaries": [],
        "skills": []
    }

    for i in range(num_pages):
        driver.get(f"https://www.naukri.com/{job_role}-jobs-{i}")
        time.sleep(3)  # Wait for the page to load

        lst = driver.find_elements(By.CLASS_NAME, "srp-jobtuple-wrapper")

        for index, job in enumerate(lst):
            driver.implicitly_wait(3)
            jobno = (i * len(lst) + index + 1)

            role = company = location = exp = salary = skill = None

            try:
                role = job.find_element(By.CLASS_NAME, "title").text
                company = job.find_element(By.CLASS_NAME, "comp-name").text
                location = job.find_element(By.CLASS_NAME, "loc-wrap").text
                exp = job.find_element(By.CLASS_NAME, "exp-wrap").text
                salary_elements = job.find_elements(By.CLASS_NAME, "sal-wrap")
                salary = salary_elements[0].text if salary_elements else "NA"

                try:
                    skill_ul = job.find_element(By.CLASS_NAME, "tags-gt")
                    skill_li = skill_ul.find_elements(By.TAG_NAME, "li")
                    skill_tag = [li.text for li in skill_li]
                    skill = ','.join(skill_tag)
                except NoSuchElementException:
                    skill = "NA"

                jobs["job_no"].append(jobno)
                jobs["roles"].append(role)
                jobs["companies"].append(company)
                jobs["locations"].append(location)
                jobs["experience"].append(exp)
                jobs["salaries"].append(salary)
                jobs["skills"].append(skill)
            except NoSuchElementException:
                # Skip job if other essential elements (role, company, location, experience) are not found
                continue
    return jobs

def process_job_data(jobs_data):
    """
    Transforms raw job data into a pandas DataFrame and cleans it.

    Args:
        jobs_data (dict): Dictionary containing raw job data.

    Returns:
        pandas.DataFrame: Cleaned DataFrame.
    """
    df_raw = pd.DataFrame.from_dict(jobs_data)
    df_raw = df_raw.apply(lambda x: x.astype(str).str.lower())

    # Split locations and skills
    df_raw['skills'] = [skill.split(",") for skill in df_raw['skills']]
    df_raw['locations'] = [location.split(",") for location in df_raw['locations']]

    # Remove 'lac pa' and ' yrs' from salaries and experience column
    df_raw['salaries'] = df_raw['salaries'].str.replace(' lacs pa', '')
    df_raw['experience'] = df_raw['experience'].str.replace(' yrs', '')

    return df_raw

def analyze_experience(df):
    """Analyzes and plots job experience data."""
    experience_counts = df['experience'].value_counts()
    print("Experience Categories and their Counts:")
    print(experience_counts)

    total_exp_range = len(df['experience'])
    experience_percentages = (experience_counts / total_exp_range) * 100
    print("\nExperience Categories and their Percentages:")
    print(experience_percentages)

    new_experience_counts = df['experience'].value_counts().head(10)
    plt.figure(figsize=(10, 6))
    new_experience_counts.plot(kind='bar', color='skyblue')
    plt.title('Experience Range')
    plt.xlabel('Experience')
    plt.ylabel('Range')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(script_dir, 'experience_range.png'))
    plt.close()
    print("\nExperience range plot saved as 'experience_range.png'")

def analyze_salary(df):
    """Analyzes and plots job salary data."""
    salaries_counts = df['salaries'].value_counts()
    print("\nSalary Categories and their Counts:")
    print(salaries_counts)

    total_salaries = len(df['salaries'])
    salaries_percentages = (salaries_counts / total_salaries) * 100
    print("\nSalary Categories and their Percentages:")
    print(salaries_percentages)

    new_salaries_counts = df['salaries'].value_counts().head(5)
    plt.figure(figsize=(10, 6))
    new_salaries_counts.plot(kind='bar', color='skyblue')
    plt.title('Salaries Range')
    plt.xlabel('Salary')
    plt.ylabel('Range')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(script_dir, 'salaries_range.png'))
    plt.close()
    print("Salaries range plot saved as 'salaries_range.png'")

def clean_and_analyze_locations(df):
    """Cleans, analyzes, and plots job location data."""
    df_location = df.assign(Values=df['locations'].str.split(',')).explode('locations')
    df_location = df_location[['job_no', 'locations']]

    def replace_location_patterns(location):
        patterns = [
            r'\(.*\)',
            r'hybrid\s*-\s*',
            r'\bnew\s',
            r'\s*',
            r'/.*$'
        ]
        for pattern in patterns:
            location = re.sub(pattern, '', location)
        return location.strip()

    df_location['locations'] = df_location['locations'].apply(replace_location_patterns)

    def replace_common_locations(location):
        replacements = {
            r'\b\w*mumbai\w*\b': 'mumbai',
            r'\b\w*delhi\w*\b': 'delhi',
            r'\b\w*bangal\w*\b': 'bengaluru',
            r'\b\w*noida\w*\b': 'noida'
        }
        for pattern, replacement in replacements.items():
            location = re.sub(pattern, replacement, location)
        return location.strip()

    df_location['locations'] = df_location['locations'].apply(replace_common_locations)

    location_counts = df_location['locations'].value_counts()
    print("\nLocation Categories and their Counts:")
    print(location_counts)

    total_location = len(df_location['locations'])
    location_percentages = (location_counts / total_location) * 100
    print("\nLocation Categories and their Percentages:")
    print(location_percentages)

    plt.figure(figsize=(10, 6))
    location_counts.plot(kind='bar', color='skyblue')
    plt.title('Job Post in Different Location')
    plt.xlabel('Location')
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(script_dir, 'job_location_counts.png'))
    plt.close()
    print("Job location counts plot saved as 'job_location_counts.png'")

    location_string = ', '.join(df_location['locations'].dropna())
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(location_string)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(os.path.join(script_dir, 'location_wordcloud.png'))
    plt.close()
    print("Location word cloud saved as 'location_wordcloud.png'")

def analyze_skills(df):
    """Analyzes and plots job skills data."""
    df_skills = df.assign(Values=df['skills'].str.split(',')).explode('skills')
    df_skills = df_skills[['job_no', 'skills']]

    distinct_skill = df_skills['skills'].unique()
    print("\nDistinct Skills:")
    for value in distinct_skill:
        print(value)

    skills_string = ', '.join(df_skills['skills'].dropna())
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(skills_string)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(os.path.join(script_dir, 'skills_wordcloud.png'))
    plt.close()
    print("Skills word cloud saved as 'skills_wordcloud.png'")

def main():
    """Main function to run the web scraping and analysis."""
    driver = None
    try:
        driver = initialize_driver()
        print(f"Scraping Naukri.com for {job_role} job data...")
        jobs_data = scrape_naukri_jobs(driver,num_pages)
        print("Scraping complete. Processing data...")
        
        if not jobs_data["job_no"]:
            print("No job data scraped. Exiting.")
            return

        df_raw = process_job_data(jobs_data)
        df_raw.to_csv(os.path.join(script_dir, f'Naukri_{job_role.replace(" ","_")}.csv'), index=False)
        print(f"✅ Raw data saved as Naukri_{job_role.replace(' ','_')}.csv")


        print("\nAnalyzing Experience...")
        analyze_experience(df_raw)

        print("\nAnalyzing Salary...")
        analyze_salary(df_raw)

        print("\nAnalyzing Locations...")
        clean_and_analyze_locations(df_raw)

        print("\nAnalyzing Skills...")
        analyze_skills(df_raw)

        print("\nAnalysis complete. Check generated PNG files for plots.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if driver:
            driver.quit()
            print("WebDriver closed.")

if __name__ == "__main__":
    main()
