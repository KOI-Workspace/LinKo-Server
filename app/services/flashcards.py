from app.schemas.flashcard import LessonFlashcardsResponse


FLASHCARD_FIXTURES: dict[str, LessonFlashcardsResponse] = {
    "3": LessonFlashcardsResponse(
        lessonId="3",
        lessonTitle="Korean Street Food Tour Seoul",
        cards=[
            {
                "id": "fc-3-1",
                "type": "word",
                "expression": "길거리 음식",
                "meaning": "Street food",
                "exampleSentence": "서울의 길거리 음식은 정말 다양하고 맛있어요.",
                "exampleTranslation": "Street food in Seoul is incredibly diverse and delicious.",
                "video": {"youtubeId": "dQw4w9WgXcQ", "startSec": 12, "endSec": 28},
                "relatedVideos": [
                    {
                        "id": "7",
                        "title": "10 Must-Know Korean Slang Words",
                        "channelName": "Talk To Me In Korean",
                        "startSec": 45,
                    },
                    {
                        "id": "8",
                        "title": "Korean Food Vocabulary with Chef",
                        "channelName": "Maangchi",
                        "startSec": 102,
                    },
                ],
                "dailyConversation": [
                    {"text": "한국 길거리 음식 먹어본 적 있어요?", "isQuestion": True},
                    {"text": "네! 떡볶이랑 호떡이 제일 맛있었어요.", "isQuestion": False},
                ],
            },
            {
                "id": "fc-3-2",
                "type": "word",
                "expression": "가득해요",
                "meaning": "To be full of / packed with",
                "exampleSentence": "이 시장은 맛있는 음식 가게로 가득해요.",
                "exampleTranslation": "This market is packed with delicious food stalls.",
                "video": {"youtubeId": "dQw4w9WgXcQ", "startSec": 45, "endSec": 62},
                "relatedVideos": [
                    {
                        "id": "6",
                        "title": "Korean Pronunciation Guide for Beginners",
                        "channelName": "Korean Class 101",
                        "startSec": 30,
                    }
                ],
                "dailyConversation": [
                    {"text": "광장시장 가볼 만해요?", "isQuestion": True},
                    {"text": "당연하죠. 빈대떡이랑 육회로 가득한 곳이에요.", "isQuestion": False},
                ],
            },
            {
                "id": "fc-3-3",
                "type": "word",
                "expression": "꼭 먹어봐야 해",
                "meaning": "You must try it / must-eat",
                "exampleSentence": "한국에 오면 떡볶이는 꼭 먹어봐야 해요.",
                "exampleTranslation": "If you come to Korea, you must try tteokbokki.",
                "video": {"youtubeId": "dQw4w9WgXcQ", "startSec": 78, "endSec": 95},
                "relatedVideos": [
                    {
                        "id": "5",
                        "title": "Learn Korean with BLACKPINK",
                        "channelName": "BLACKPINK",
                        "startSec": 15,
                    },
                    {
                        "id": "8",
                        "title": "Korean Food Vocabulary with Chef",
                        "channelName": "Maangchi",
                        "startSec": 200,
                    },
                ],
                "dailyConversation": [
                    {"text": "서울에서 뭘 꼭 먹어야 해요?", "isQuestion": True},
                    {
                        "text": "빙수요! 여름에 꼭 먹어봐야 하는 디저트예요.",
                        "isQuestion": False,
                    },
                ],
            },
            {
                "id": "fc-3-e1",
                "type": "ending",
                "baseWord": "가득하다",
                "baseWordMeaning": "To be full of / packed with",
                "conjugatedForm": "가득해요",
                "conjugationBadges": [
                    {
                        "removed": "하",
                        "added": "해요",
                        "removedDetail": {
                            "category": "어간변화",
                            "subCategories": ["Contraction"],
                            "explanation": "The stem-final \"하\" in 하다 verbs contracts with a following vowel ending. 하 + 아/어 -> 해 is an irregular but extremely common pattern.",
                        },
                        "addedDetail": {
                            "category": "어말-종결",
                            "subCategories": ["Declarative", "Informal"],
                            "explanation": "The most common polite sentence-final ending in everyday conversation. Expresses present tense in a friendly, polite manner.",
                        },
                    }
                ],
                "ending": "아/어요",
                "endingMeaning": "Polite present tense",
                "endingExplanation": "일상 대화에서 가장 많이 쓰이는 공손한 현재 어미예요. 하다 동사·형용사는 -하 뒤에 아/어 계열 어미가 올 때 -해로 줄어들어요.",
                "scriptSentence": "이 시장은 맛있는 음식 가게로 가득해요.",
                "scriptTranslation": "This market is packed with delicious food stalls.",
                "video": {"youtubeId": "dQw4w9WgXcQ", "startSec": 45, "endSec": 62},
                "relatedVideos": [],
            },
            {
                "id": "fc-3-4",
                "type": "word",
                "expression": "줄을 서다",
                "meaning": "To stand in line / queue up",
                "exampleSentence": "사람들이 이 꼬치를 사려고 몇 시간씩 줄을 서요.",
                "exampleTranslation": "People stand in line for hours to buy these skewers.",
                "video": {"youtubeId": "dQw4w9WgXcQ", "startSec": 110, "endSec": 127},
                "relatedVideos": [],
                "dailyConversation": [
                    {"text": "왜 밖에 줄이 저렇게 길어요?", "isQuestion": True},
                    {
                        "text": "매일 아침 200개만 만들어서 다들 줄을 서요.",
                        "isQuestion": False,
                    },
                ],
            },
            {
                "id": "fc-3-5",
                "type": "word",
                "expression": "저렴하다",
                "meaning": "Affordable / inexpensive",
                "exampleSentence": "여기 길거리 음식은 놀랍도록 저렴해요.",
                "exampleTranslation": "Street food here is surprisingly affordable.",
                "video": {"youtubeId": "dQw4w9WgXcQ", "startSec": 145, "endSec": 162},
                "relatedVideos": [
                    {
                        "id": "10",
                        "title": "Essential Korean Phrases for Travel",
                        "channelName": "Korean With Joo",
                        "startSec": 88,
                    }
                ],
                "dailyConversation": [
                    {"text": "동남아 여행 비용이 많이 들어요?", "isQuestion": True},
                    {
                        "text": "아니요, 엄청 저렴해요. 하루에 5달러로도 잘 먹을 수 있어요.",
                        "isQuestion": False,
                    },
                ],
            },
            {
                "id": "fc-3-6",
                "type": "word",
                "expression": "노점상",
                "meaning": "Street vendor / food stall",
                "exampleSentence": "노점상 아저씨가 따뜻한 어묵 국물을 건네주셨어요.",
                "exampleTranslation": "The street vendor handed me a steaming cup of fish cake broth.",
                "video": {"youtubeId": "dQw4w9WgXcQ", "startSec": 180, "endSec": 196},
                "relatedVideos": [],
                "dailyConversation": [
                    {"text": "그 핫도그 어디서 샀어요?", "isQuestion": True},
                    {
                        "text": "지하철 출구 근처 노점상에서요. 2,000원밖에 안 해요!",
                        "isQuestion": False,
                    },
                ],
            },
            {
                "id": "fc-3-e2",
                "type": "ending",
                "baseWord": "다양하다",
                "baseWordMeaning": "Diverse / varied",
                "conjugatedForm": "다양하고",
                "conjugationBadges": [
                    {
                        "added": "고",
                        "addedDetail": {
                            "category": "어말-연결",
                            "subCategories": ["Listing", "Sequential"],
                            "explanation": "Connective ending that lists facts or states side by side, or indicates the order of actions. Attaches to any stem without modification.",
                        },
                    }
                ],
                "ending": "고",
                "endingMeaning": "And / listing (connective ending)",
                "endingExplanation": "두 가지 사실이나 상태를 나란히 이어줄 때 써요. 자음·모음으로 끝나는 어간 모두에 붙으며, -하다 동사도 그냥 -하고로 사용해요.",
                "scriptSentence": "서울의 길거리 음식은 정말 다양하고 맛있어요.",
                "scriptTranslation": "Street food in Seoul is incredibly diverse and delicious.",
                "video": {"youtubeId": "dQw4w9WgXcQ", "startSec": 12, "endSec": 28},
                "relatedVideos": [],
            },
        ],
    ),
    "4": LessonFlashcardsResponse(
        lessonId="4",
        lessonTitle="K-drama Vocabulary Basics",
        cards=[
            {
                "id": "fc-4-1",
                "type": "word",
                "expression": "반전",
                "meaning": "Plot twist / reversal",
                "exampleSentence": "8화의 반전은 모든 사람을 놀라게 했어요.",
                "exampleTranslation": "The plot twist in episode 8 surprised everyone.",
                "video": {"youtubeId": "dQw4w9WgXcQ", "startSec": 20, "endSec": 38},
                "relatedVideos": [
                    {
                        "id": "9",
                        "title": "K-pop Lyrics Korean Lesson",
                        "channelName": "SMTOWN",
                        "startSec": 67,
                    }
                ],
                "dailyConversation": [
                    {"text": "사랑의 불시착 다 봤어요?", "isQuestion": True},
                    {
                        "text": "네! 마지막 반전에서 완전히 충격받았어요.",
                        "isQuestion": False,
                    },
                ],
            },
            {
                "id": "fc-4-2",
                "type": "word",
                "expression": "몰아보다",
                "meaning": "To binge-watch",
                "exampleSentence": "어젯밤에 한 시즌을 통째로 몰아봤어요.",
                "exampleTranslation": "I binge-watched an entire season last night.",
                "video": {"youtubeId": "dQw4w9WgXcQ", "startSec": 55, "endSec": 72},
                "relatedVideos": [],
                "dailyConversation": [
                    {"text": "피곤해 보여요. 잠 못 잤어요?", "isQuestion": True},
                    {
                        "text": "오징어 게임 3시즌을 몰아봤어요. 완전 후회 없어요.",
                        "isQuestion": False,
                    },
                ],
            },
            {
                "id": "fc-4-e1",
                "type": "ending",
                "baseWord": "충격받다",
                "baseWordMeaning": "To be shocked / taken aback",
                "conjugatedForm": "충격받았어요",
                "conjugationBadges": [
                    {
                        "added": "았",
                        "addedDetail": {
                            "category": "선어말어미",
                            "subCategories": ["Tense"],
                            "explanation": "Pre-final ending marking past tense. Use ~았 when the stem's last vowel is ㅏ or ㅗ; otherwise use ~었. Always comes before the final sentence-ending.",
                        },
                    },
                    {
                        "added": "어요",
                        "addedDetail": {
                            "category": "어말-종결",
                            "subCategories": ["Declarative", "Informal"],
                            "explanation": "Polite sentence-final ending for everyday speech. Combined with ~았/었 to form the polite past tense ~았어요/었어요.",
                        },
                    },
                ],
                "ending": "았/었어요",
                "endingMeaning": "Polite past tense",
                "endingExplanation": "지난 일을 공손하게 말할 때 써요. 어간 마지막 모음이 ㅏ·ㅗ이면 -았어요, 그 외엔 -었어요를 써요. 충격받다처럼 ㅏ 모음이 있으면 -았어요가 붙어요.",
                "scriptSentence": "마지막 반전에서 완전히 충격받았어요.",
                "scriptTranslation": "I was completely shocked by the final plot twist.",
                "video": {"youtubeId": "dQw4w9WgXcQ", "startSec": 20, "endSec": 38},
                "relatedVideos": [],
            },
            {
                "id": "fc-4-3",
                "type": "word",
                "expression": "설레다",
                "meaning": "To feel excited / flutter with anticipation",
                "exampleSentence": "그 장면을 볼 때마다 가슴이 설레요.",
                "exampleTranslation": "My heart flutters every time I watch that scene.",
                "video": {"youtubeId": "dQw4w9WgXcQ", "startSec": 90, "endSec": 108},
                "relatedVideos": [
                    {
                        "id": "5",
                        "title": "Learn Korean with BLACKPINK",
                        "channelName": "BLACKPINK",
                        "startSec": 30,
                    }
                ],
                "dailyConversation": [
                    {"text": "내일 여행이라 너무 설레지 않아요?", "isQuestion": True},
                    {
                        "text": "맞아요! 어젯밤에 설레서 잠도 못 잤어요.",
                        "isQuestion": False,
                    },
                ],
            },
            {
                "id": "fc-4-4",
                "type": "word",
                "expression": "주인공",
                "meaning": "Main character / protagonist",
                "exampleSentence": "이 드라마 주인공은 정말 매력적이에요.",
                "exampleTranslation": "The main character of this drama is really charming.",
                "video": {"youtubeId": "dQw4w9WgXcQ", "startSec": 125, "endSec": 140},
                "relatedVideos": [],
                "dailyConversation": [
                    {"text": "그 드라마 어때요?", "isQuestion": True},
                    {"text": "너무 재밌어요. 주인공이 완전 제 스타일이에요.", "isQuestion": False},
                ],
            },
        ],
    ),
    "5": LessonFlashcardsResponse(
        lessonId="5",
        lessonTitle="Learn Korean with BLACKPINK",
        cards=[
            {
                "id": "fc-5-1",
                "type": "word",
                "expression": "자신감",
                "meaning": "Confidence / self-confidence",
                "exampleSentence": "그들의 무대에서는 자신감이 넘쳐 흘러요.",
                "exampleTranslation": "Their stage performance overflows with confidence.",
                "video": {"youtubeId": "dQw4w9WgXcQ", "startSec": 8, "endSec": 24},
                "relatedVideos": [],
                "dailyConversation": [
                    {"text": "발표할 때 어떻게 그렇게 떨리지 않아요?", "isQuestion": True},
                    {"text": "연습을 많이 하면 자신감이 생겨요.", "isQuestion": False},
                ],
            },
            {
                "id": "fc-5-2",
                "type": "word",
                "expression": "중독성 있다",
                "meaning": "Addictive / catchy",
                "exampleSentence": "이 노래 후렴구가 너무 중독성 있어서 계속 흥얼거리게 돼요.",
                "exampleTranslation": "The chorus is so addictive I keep humming it all day.",
                "video": {"youtubeId": "dQw4w9WgXcQ", "startSec": 40, "endSec": 56},
                "relatedVideos": [
                    {
                        "id": "9",
                        "title": "K-pop Lyrics Korean Lesson",
                        "channelName": "SMTOWN",
                        "startSec": 22,
                    }
                ],
                "dailyConversation": [
                    {"text": "신곡 어떻게 생각해요?", "isQuestion": True},
                    {
                        "text": "완전 중독성 있어요. 하루 종일 머릿속에서 맴돌아요.",
                        "isQuestion": False,
                    },
                ],
            },
            {
                "id": "fc-5-e1",
                "type": "ending",
                "baseWord": "있다",
                "baseWordMeaning": "To be / to exist / to have",
                "conjugatedForm": "있어서",
                "conjugationBadges": [
                    {
                        "added": "어서",
                        "addedDetail": {
                            "category": "어말-연결",
                            "subCategories": ["Reason", "Cause"],
                            "explanation": "Connective ending indicating the preceding clause is the reason or cause of the following clause. Always attaches to the present-tense stem - do not combine with ~았/었.",
                        },
                    }
                ],
                "ending": "아/어서",
                "endingMeaning": "Because / so (cause and effect)",
                "endingExplanation": "앞 절이 뒤 절의 원인·이유임을 나타내요. 시제 변화 없이 현재 어간에 붙이며, -았/었어서처럼 과거형으로 쓰지 않는 게 일반적이에요.",
                "scriptSentence": "중독성이 있어서 하루 종일 머릿속에서 맴돌아요.",
                "scriptTranslation": "It's so addictive that it keeps playing in my head all day.",
                "video": {"youtubeId": "dQw4w9WgXcQ", "startSec": 40, "endSec": 56},
                "relatedVideos": [],
            },
        ],
    ),
}


def get_lesson_flashcards(lesson_id: str) -> LessonFlashcardsResponse | None:
    return FLASHCARD_FIXTURES.get(lesson_id)
