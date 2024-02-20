import re
from dotenv import load_dotenv
from sydney import SydneyClient

# load BING_COOKIES environment variable from .env
load_dotenv()

async def ask_sydney(prompt: str):
    async with SydneyClient() as sydney:
        image = None
        text = ""

        response = await sydney.ask(prompt, raw=True)
        message = max(response['item']['messages'][-2:], key=lambda x: len(x['text']))
        body = message['adaptiveCards'][0]['body']

        for item in body:
            if item['type'] == 'Image':
                image = item['url']
            elif item['type'] == 'TextBlock':
                text += parse(item['text'] + '\n')

        return image, text.strip()
    
def parse(string: str):
    citations, string = get_citations(string)

    if citations == None:
        return string
    
    else:
        i = 1
        while match := re.search(r"\[\^(\d+)\^\]\[(\d)\]", string):
            index = match.groups()
            string = re.sub(rf"\[\^{index[0]}\^\]\[{index[1]}\]\s?", f"[`[{i}]`]({citations[int(index[1])-1]})", string)
            i += 1

        return string
    
def get_citations(string: str):
    citation_pattern = r'\[\d+\]:\s(.*)\s""\n'

    if citations := re.findall(citation_pattern, string):
        string = re.sub(citation_pattern, "", string)
        return citations, string
    
    else:
        return None, string