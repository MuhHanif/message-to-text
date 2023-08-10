from fastapi import FastAPI, HTTPException, Body
from bs4 import BeautifulSoup
import uvicorn
import tiktoken

app = FastAPI()
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")


def parser(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # Extract text content from the parsed HTML
    text = soup.get_text(separator=" ")
    words = text.split()
    text = " ".join(words)
    return text


def reformat_data(data: str) -> dict:
    result = []
    for item in data:
        # new dict
        new_item = {}
        for key, value in item.items():
            # now data is a list which we can parse if key is a merged bodies
            data = value.split("===")

            # reformat email bodies and extract just the text
            if key == "merged_bodies":
                data = [parser(x) for x in data]

            new_item[key] = data

        # append name and text message and turn it into conversation
        # example:
        # ["bob", "alice"] ["text1", "text2"]
        # ["bob: text1", "alice: text2"]
        new_item["conversation_format"] = [
            f"{x[0]}: {x[1]}"
            for x in list(
                zip(
                    new_item["merged_posters"],
                    new_item["merged_bodies"],
                )
            )
        ]
        # make a back and forth conversation
        new_item["conversation_format_joined"] = "\n".join(
            new_item["conversation_format"]
        )
        # count number of token
        new_item["token_count"] = len(
            encoding.encode(new_item["conversation_format_joined"])
        )

        result.append(new_item)

    return result


@app.post("/extract-text")
async def extract_text_from_html(data: dict = Body(...)):
    try:
        return {"extracted_text": reformat_data([data])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8754)
