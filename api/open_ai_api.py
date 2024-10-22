import pandas as pd
from openai import OpenAI
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from util.format_converter import convert_to_datetime
from web_scraper import scrape_comments

# Initialize FastAPI app
app = FastAPI()

# Initialize OpenAI client
client = OpenAI(
    api_key="Your Open AI Key"
)

def ask_gpt(question):
    response = client.chat.completions.create(
        model="gpt-4",  # You can use "gpt-3.5-turbo" for GPT-3.5
        messages=[
            {"role": "system", "content": "You are a sales specialist."},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content


def get_product_category_keywords(product_name):
    product_question_template = "Consider the following product name and tell me three fitting category keywords that can be used to apply sentiment analysis on it: (only respond with the three keywords separated with comma.)"
    product_question = f"{product_question_template} {product_name}"
    product_answer = ask_gpt(product_question)

    keywords = [keyword.strip() for keyword in product_answer.split(',')]

    return keywords


def analyze_sentiments(comments):
    review_question_template = "Consider the following paragraph and tell me if it is a positive, negative or neutral review of the product: (only respond with one word.)"

    sentiments = pd.DataFrame(columns=["review", "sentiment", "date"])

    for comment_data in comments:
        question = f"{review_question_template} {comment_data['text']}"
        answer = ask_gpt(question)

        data = pd.DataFrame({"review": [comment_data['text']], "sentiment": answer, "date": [comment_data['date']]})
        sentiments = pd.concat([sentiments, data], ignore_index=True)

    return sentiments


def analyze_sentiments_with_ai_keywords(comments, keywords):
    review_question_template = "Consider the following paragraph and tell me if it is a positive, negative or neutral review of the product: (only respond with one word.)"
    review_question_keywords_template = (f"the same thing for the following categories: {keywords[0]}, {keywords[1]}, {keywords[2]} and answer with one word for each of them as well. format your answer for each with a comma between them."
                                         f"always reply with 4 words, separated by a comma, if the keyword is not mentioned, write neutral instead of positive or negative. but the first sentiment value can never be null.")

    sentiments = pd.DataFrame({"review": ["review"], "sentiment": ["general sentiment"],
                               "keyword_sentiment_1": [keywords[0]], "keyword_sentiment_2": [keywords[1]], "keyword_sentiment_3": [keywords[2]]})

    for comment_data in comments:
        question = f"{review_question_template} {review_question_keywords_template} {comment_data['text']}"
        answer = ask_gpt(question)

        answer_split = [answer_part.strip() for answer_part in answer.split(',')]

        data = pd.DataFrame({"review": [comment_data['text']], "sentiment": [answer_split[0]], "keyword_sentiment_1": [answer_split[1]],
                             "keyword_sentiment_2": [answer_split[2]],  "keyword_sentiment_3": answer_split[3]})
        sentiments = pd.concat([sentiments, data], ignore_index=True)

    return sentiments


@app.get("/get_sentiment_counts/")
async def get_sentiment_counts(url: str):
    """API endpoint to get the total count of positive, negative, and neutral sentiments."""
    try:
        # Scrape the product name and comments
        product_name, comments = scrape_comments(url)

        # Analyze the sentiments of the comments
        sentiments = analyze_sentiments(comments)

        # Count the number of positive, negative, and neutral sentiments
        positive_count = 0
        negative_count = 0
        neutral_count = 0

        for sentiment in sentiments["sentiment"]:
            if sentiment.lower() == "positive":
                positive_count += 1
            elif sentiment.lower() == "negative":
                negative_count += 1
            elif sentiment.lower() == "neutral":
                neutral_count += 1


        results = [{"product_name": product_name, "Positive": positive_count,
            "Negative": negative_count, "Neutral": neutral_count}]

        # Return the counts as JSON response
        return JSONResponse(results)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/get_sentiment_counts_by_keyword/")
async def get_sentiment_counts_by_keyword(url: str, search_term: str):
    """API endpoint to get the total count of positive, negative, and neutral sentiments based on comments containing a specific keyword."""
    try:
        # Scrape the product name and comments
        product_name, comments = scrape_comments(url)

        # Filter comments to include only those that contain the search term
        filtered_comments = [comment for comment in comments if search_term.lower() in comment['text'].lower()]

        # Analyze the sentiments of the filtered comments
        sentiments = analyze_sentiments(filtered_comments)

        # Count the number of positive, negative, and neutral sentiments
        positive_count = 0
        negative_count = 0
        neutral_count = 0

        for sentiment in sentiments["sentiment"]:
            if sentiment.lower() == "positive":
                positive_count += 1
            elif sentiment.lower() == "negative":
                negative_count += 1
            elif sentiment.lower() == "neutral":
                neutral_count += 1

        results = [{"product_name": product_name, "keyword": search_term,
                     "Positive": positive_count, "Negative": negative_count,
                     "Neutral": neutral_count}]

        # Return the counts as JSON response
        return JSONResponse(results)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/get_filtered_comments_sentiments/")
async def get_filtered_comments_sentiments(url: str, filter_string: str):
    """API endpoint to filter comments based on a keyword and return sentiment analysis."""
    try:
        # Scrape the product name and comments
        product_name, comments = scrape_comments(url)

        # Filter comments that contain the specified string (case-insensitive)
        filtered_comments = [
            comment for comment in comments
            if filter_string.lower() in comment['text'].lower()
        ]

        # If no comments match the filter, return an appropriate response
        if not filtered_comments:
            return JSONResponse(content={"product_name": product_name, "filter": filter_string, "sentiments":  {'comment': None}})

        # Perform sentiment analysis on the filtered comments
        sentiments = analyze_sentiments(filtered_comments)

        # Convert the results to a list of dictionaries and return
        return JSONResponse(content={
            "product_name": product_name,
            "filter": filter_string,
            "sentiments": sentiments.to_dict(orient='records')
        })

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/get_sentiment_counts_by_time/")
async def get_sentiment_counts_by_time(url: str, start_date: str, end_date: str):
    """API endpoint to get the total count of positive, negative, and neutral sentiments within a specific time range."""
    try:
        # Scrape the product name and comments
        product_name, comments = scrape_comments(url)
        # Analyze the sentiments of the comments
        sentiments = analyze_sentiments(comments)

        # Count the number of positive, negative, and neutral sentiments within the specified date range
        positive_count = 0
        negative_count = 0
        neutral_count = 0

        converted_start = convert_to_datetime(start_date)
        converted_end = convert_to_datetime(end_date)

        for count in range(len(sentiments)):
            row = sentiments.iloc[count]
            # Convert the date string to a datetime object
            date_string = row['date']
            converted_date = convert_to_datetime(date_string)

            # Check if the comment's date is within the start and end date range
            if converted_start <= converted_date <= converted_end:
                if row["sentiment"].lower() == "positive":
                    positive_count += 1
                elif row["sentiment"].lower() == "negative":
                    negative_count += 1
                elif row["sentiment"].lower() == "neutral":
                    neutral_count += 1

        # Return the counts as JSON response
        return JSONResponse(content={
            "product_name": product_name,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count
        })

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/scrape_reviews/")
async def scrape_reviews(url: str):
    """API endpoint to scrape reviews and analyze sentiments for a product."""
    try:
        product_name, comments = scrape_comments(url)
        sentiments = analyze_sentiments(comments)
        return JSONResponse(content={"product_name": product_name, "sentiments": sentiments.to_dict(orient='records')})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/scrape_reviews_with_ai_categories/")
async def scrape_reviews_with_ai_categories(url: str):
    """API endpoint to scrape reviews and analyze sentiments for a product."""
    try:
        product_name, comments = scrape_comments(url)
        keywords = get_product_category_keywords(product_name)
        sentiments = analyze_sentiments_with_ai_keywords(comments, keywords)
        return JSONResponse(content={"product_name": product_name, "keywords": keywords, "sentiments": sentiments.to_dict(orient='records')})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/scrape_reviews_by_time")
async def scrape_reviews_by_time(url: str, start_date: str, end_date: str):
    try:
        product_name, comments = scrape_comments(url)
        sentiments = analyze_sentiments(comments)

        filtered_comments = []
        print(sentiments)
        count = 0
        for date_string in sentiments['date']:
            converted_date = convert_to_datetime(date_string)

            converted_start_date = datetime.strptime(start_date, "%Y-%m-%d") #convert_int_datetime(start_date) #convert_to_datetime(start_date)
            converted_end_date = datetime.strptime(end_date, "%Y-%m-%d")#convert_int_datetime(end_date) #convert_to_datetime(end_date)

            if converted_start_date <= converted_date <= converted_end_date:
                filtered_comments.append(sentiments.iloc[count].to_dict())

            count = count + 1

        return JSONResponse(content={
            "product_name": product_name,
            "sentiments": filtered_comments
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/get_yesterday_negative_comment/")
async def get_yesterday_negative_comment(url: str):
    """API endpoint to check if there are any comments from yesterday, and return any negative comments if found."""
    try:
        # Scrape the product name and comments
        product_name, comments = scrape_comments(url)

        # Define yesterday's date
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_start = datetime(yesterday.year, yesterday.month, yesterday.day)
        yesterday_end = yesterday_start + timedelta(days=1)

        # Filter comments to include only those from yesterday
        yesterday_comments = []
        for comment in comments:
            date_string = comment['date']
            converted_date = convert_to_datetime(date_string)

            if yesterday_start <= converted_date < yesterday_end:
                yesterday_comments.append(comment)

        # If there are no comments from yesterday, return null
        if not yesterday_comments:
            return JSONResponse(content={"product_name": product_name, "comment": None})

        # Analyze the sentiments of yesterday's comments
        sentiments = analyze_sentiments(yesterday_comments)
        
        # Check for any negative sentiments
        for sentiment in sentiments.to_dict(orient='records'):
            if sentiment["sentiment"].lower() == "negative":
                return JSONResponse(content={
                    "product_name": product_name,
                    "comment": sentiment["review"],
                    "sentiment": "negative"
                })

        # If no negative comments, return null
        return JSONResponse(content={"product_name": product_name, "comment": None})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)