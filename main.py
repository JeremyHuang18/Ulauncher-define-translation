import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
import requests
import logging
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction

logger = logging.getLogger(__name__)

class DefineExtension(Extension):

    def __init__(self):
        super(DefineExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items = []
        query = event.get_argument()

        if not query:
            return

        try:
            # --- English dictionary ---
            api_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{query.strip()}"
            response = requests.get(api_url, timeout=5)
            
            if response.status_code == 404:
                raise requests.exceptions.HTTPError(f"No definition found for '{query}'")
            
            response.raise_for_status()

            data = response.json()
            
            word_data = data[0]
            word = word_data.get('word', 'N/A')
            phonetic = word_data.get('phonetic', '')
            source_url = word_data.get('sourceUrls', [''])[0]

            for meaning in word_data.get('meanings', []):
                part_of_speech = meaning.get('partOfSpeech', '')
                definition = meaning['definitions'][0]['definition']
                
                items.append(
                    ExtensionResultItem(
                        icon='images/icon.png',
                        name=f"[{part_of_speech}] {word} {phonetic}",
                        description=definition,
                        on_enter=OpenUrlAction(source_url) if source_url else HideWindowAction()
                    )
                )

            # --- Chinese translator ---
            try:
                # Translate by MyMemory API
                translate_url = f"https://api.mymemory.translated.net/get?q={query.strip()}&langpair=en|zh-CN"
                translate_response = requests.get(translate_url, timeout=5)
                translate_response.raise_for_status()
                
                translate_data = translate_response.json()
                chinese_translation = translate_data['responseData']['translatedText']

                items.append(
                    ExtensionResultItem(
                        icon='images/icon.png',
                        name=f"[Chinese] {word}",
                        description=chinese_translation,
                        # Jump to Google Translator by pressing ENTER
                        on_enter=OpenUrlAction(f"https://translate.google.com/?sl=en&tl=zh-CN&text={word}&op=translate")
                    )
                )
            except Exception as e:
                logger.error(f"Could not fetch Chinese translation: {e}")

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            items.append(
                ExtensionResultItem(
                    icon='images/icon.png',
                    name=f"No definition found for '{query}'",
                    description="Please check the spelling or try another word.",
                    on_enter=HideWindowAction()
                )
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error: {e}")
            items.append(
                ExtensionResultItem(
                    icon='images/icon.png',
                    name="Network Error",
                    description="Could not connect to the dictionary API.",
                    on_enter=HideWindowAction()
                )
            )
        except (KeyError, IndexError) as e:
            logger.error(f"Data parsing error: {e}")
            items.append(
                ExtensionResultItem(
                    icon='images/icon.png',
                    name=f"Could not parse the definition for '{query}'",
                    description="The API response was not in the expected format.",
                    on_enter=HideWindowAction()
                )
            )
            
        return RenderResultListAction(items)

if __name__ == '__main__':
    DefineExtension().run()
