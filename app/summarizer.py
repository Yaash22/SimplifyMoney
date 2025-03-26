from transformers import pipeline
from typing import List, Dict
import torch
from functools import lru_cache
import re
from collections import Counter
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_summarizer():
    try:
        return pipeline(
            "summarization",
            model="facebook/bart-base",
            device=-1  
        )
    except Exception as e:
        logger.error(f"Error initializing summarizer: {e}")
        return None

@lru_cache(maxsize=1)
def get_sentiment_analyzer():
    try:
        return pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=-1 
        )
    except Exception as e:
        logger.error(f"Error initializing sentiment analyzer: {e}")
        return None

def extract_conversation_participants(text: str) -> List[str]:
    try:
        participants = set()
        lines = text.split('\n')
        for line in lines:
            match = re.match(r'^([A-Za-z\s]+):', line)
            if match:
                participants.add(match.group(1).strip())
        return list(participants)
    except Exception as e:
        logger.error(f"Error extracting participants: {e}")
        return []

def analyze_conversation_flow(text: str) -> Dict:
    try:
        messages = [line.strip() for line in text.split('\n') if line.strip()]
        participants = {}
        for message in messages:
            match = re.match(r'^([A-Za-z\s]+):(.*)', message)
            if match:
                speaker = match.group(1).strip()
                content = match.group(2).strip()
                if speaker not in participants:
                    participants[speaker] = []
                participants[speaker].append(content)
        
        return {
            "participants": list(participants.keys()),
            "message_count": len(messages),
            "messages_per_participant": {k: len(v) for k, v in participants.items()}
        }
    except Exception as e:
        logger.error(f"Error analyzing conversation flow: {e}")
        return {"message_count": 0}

async def summarize_conversation(messages: List[str]) -> Dict:
    try:
        full_text = "\n".join(messages)

        summarizer = get_summarizer()
        sentiment_analyzer = get_sentiment_analyzer()
        
        if summarizer is None or sentiment_analyzer is None:
            logger.error("Failed to initialize required models")
            return {
                "summary": "Failed to initialize models. Please check the server logs.",
                "sentiment": "neutral",
                "participants": [],
                "flow_analysis": {"message_count": 0},
                "message_count": 0
            }

        max_length = 512
        chunks = [full_text[i:i+max_length] for i in range(0, len(full_text), max_length)]
        summaries = []
        sentiments = []
        
        for chunk in chunks:
            try:
                summary = summarizer(
                    chunk,
                    max_length=100,
                    min_length=20,
                    do_sample=False
                )
                summaries.append(summary[0]['summary_text'])
                sentiment = sentiment_analyzer(chunk[:256])[0]
                sentiments.append(sentiment)
            except Exception as e:
                logger.error(f"Error processing chunk: {e}")
                continue
        
        if not summaries:
            logger.error("No summaries were generated")
            return {
                "summary": "Failed to generate summary. Please try again.",
                "sentiment": "neutral",
                "participants": [],
                "flow_analysis": {"message_count": 0},
                "message_count": 0
            }
        

        final_summary = "\n".join(summaries)
        

        flow_analysis = analyze_conversation_flow(full_text)
        

        sentiment_counts = Counter(s['label'] for s in sentiments)
        overall_sentiment = sentiment_counts.most_common(1)[0][0] if sentiments else "neutral"
        

        participants = extract_conversation_participants(full_text)
        
        return {
            "summary": final_summary,
            "sentiment": overall_sentiment,
            "participants": participants,
            "flow_analysis": flow_analysis,
            "message_count": len(messages)
        }
    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        return {
            "summary": "An error occurred during analysis. Please try again.",
            "sentiment": "neutral",
            "participants": [],
            "flow_analysis": {"message_count": 0},
            "message_count": 0
        }