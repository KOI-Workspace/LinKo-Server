"""Static subtitle fixtures used for the public preview-lesson endpoints.

These lessons are exposed without authentication so the landing page can
let unauthenticated visitors preview real learning content.  All per-user
data (bookmarks, saved state, etc.) is returned as empty / false.
"""

from typing import Any

# ---------------------------------------------------------------------------
# Lesson 3 – Korean Street Food Tour Seoul
# ---------------------------------------------------------------------------
_SUBTITLES_3: dict[str, Any] = {
    "youtubeId": "dQw4w9WgXcQ",
    "durationSec": 495,
    "lines": [
        {
            "id": "s3-1",
            "startSec": 0,
            "endSec": 12,
            "korean": "안녕하세요! 오늘은 서울 길거리 음식 투어를 해볼게요.",
            "english": "Hello! Today we're going on a Seoul street food tour.",
        },
        {
            "id": "s3-2",
            "startSec": 12,
            "endSec": 28,
            "korean": "서울의 길거리 음식은 정말 다양하고 맛있어요.",
            "english": "Street food in Seoul is incredibly diverse and delicious.",
        },
        {
            "id": "s3-3",
            "startSec": 28,
            "endSec": 44,
            "korean": "첫 번째로 명동에 왔어요. 여기는 항상 사람이 가득해요.",
            "english": "First, we came to Myeongdong. It's always packed with people here.",
        },
        {
            "id": "s3-4",
            "startSec": 44,
            "endSec": 62,
            "korean": "이 시장은 맛있는 음식 가게로 가득해요.",
            "english": "This market is packed with delicious food stalls.",
        },
        {
            "id": "s3-5",
            "startSec": 62,
            "endSec": 78,
            "korean": "한국에 오면 떡볶이는 꼭 먹어봐야 해요.",
            "english": "If you come to Korea, you must try tteokbokki.",
        },
        {
            "id": "s3-6",
            "startSec": 78,
            "endSec": 95,
            "korean": "매콤달콤한 맛이 정말 일품이에요. 꼭 먹어봐야 해요.",
            "english": "The sweet and spicy flavor is truly excellent. You must try it.",
        },
        {
            "id": "s3-7",
            "startSec": 95,
            "endSec": 110,
            "korean": "다음은 광장시장으로 이동했어요.",
            "english": "Next, we moved on to Gwangjang Market.",
        },
        {
            "id": "s3-8",
            "startSec": 110,
            "endSec": 127,
            "korean": "사람들이 이 꼬치를 사려고 몇 시간씩 줄을 서요.",
            "english": "People stand in line for hours to buy these skewers.",
        },
        {
            "id": "s3-9",
            "startSec": 127,
            "endSec": 145,
            "korean": "그래도 기다릴 만한 가치가 있어요.",
            "english": "Still, it's worth the wait.",
        },
        {
            "id": "s3-10",
            "startSec": 145,
            "endSec": 162,
            "korean": "여기 길거리 음식은 놀랍도록 저렴해요.",
            "english": "Street food here is surprisingly affordable.",
        },
        {
            "id": "s3-11",
            "startSec": 162,
            "endSec": 180,
            "korean": "2,000원에서 5,000원 정도면 든든하게 먹을 수 있어요.",
            "english": "For around 2,000 to 5,000 won you can eat a filling meal.",
        },
        {
            "id": "s3-12",
            "startSec": 180,
            "endSec": 196,
            "korean": "노점상 아저씨가 따뜻한 어묵 국물을 건네주셨어요.",
            "english": "The street vendor handed me a steaming cup of fish cake broth.",
        },
        {
            "id": "s3-13",
            "startSec": 196,
            "endSec": 215,
            "korean": "정말 감동이었어요. 한국 인심은 최고예요!",
            "english": "It was really touching. Korean hospitality is the best!",
        },
    ],
    "vocabMap": {
        "길거리 음식": {
            "meaning": "Street food",
            "cardId": "fc-3-1",
            "lessonId": "3",
            "expression": "길거리 음식",
            "exampleSentence": "서울의 길거리 음식은 정말 다양하고 맛있어요.",
            "exampleTranslation": "Street food in Seoul is incredibly diverse and delicious.",
        },
        "가득해요": {
            "meaning": "To be full of / packed with",
            "cardId": "fc-3-2",
            "lessonId": "3",
            "expression": "가득해요",
            "exampleSentence": "이 시장은 맛있는 음식 가게로 가득해요.",
            "exampleTranslation": "This market is packed with delicious food stalls.",
        },
        "꼭 먹어봐야 해": {
            "meaning": "You must try it / must-eat",
            "cardId": "fc-3-3",
            "lessonId": "3",
            "expression": "꼭 먹어봐야 해",
            "exampleSentence": "한국에 오면 떡볶이는 꼭 먹어봐야 해요.",
            "exampleTranslation": "If you come to Korea, you must try tteokbokki.",
        },
        "줄을 서요": {
            "meaning": "To stand in line / queue up",
            "cardId": "fc-3-4",
            "lessonId": "3",
            "expression": "줄을 서요",
            "exampleSentence": "사람들이 이 꼬치를 사려고 몇 시간씩 줄을 서요.",
            "exampleTranslation": "People stand in line for hours to buy these skewers.",
        },
        "저렴해요": {
            "meaning": "Affordable / inexpensive",
            "cardId": "fc-3-5",
            "lessonId": "3",
            "expression": "저렴해요",
            "exampleSentence": "여기 길거리 음식은 놀랍도록 저렴해요.",
            "exampleTranslation": "Street food here is surprisingly affordable.",
        },
        "노점상": {
            "meaning": "Street vendor / food stall",
            "cardId": "fc-3-6",
            "lessonId": "3",
            "expression": "노점상",
            "exampleSentence": "노점상 아저씨가 따뜻한 어묵 국물을 건네주셨어요.",
            "exampleTranslation": "The street vendor handed me a steaming cup of fish cake broth.",
        },
    },
    "culturalNotes": [
        {
            "id": "culture-3-1",
            "subtitleId": "s3-4",
            "title": "가득해요 – More than 'full'",
            "keyword": "가득",
            "explanation": (
                "가득 (full, packed) is used in a wide range of contexts—a market stall "
                "full of people, a heart full of emotion, a bag packed with snacks. "
                "It expresses abundance and is often combined with -해요 for a polite tone."
            ),
        },
        {
            "id": "culture-3-2",
            "subtitleId": "s3-8",
            "title": "줄을 서다 – Queuing culture in Korea",
            "keyword": "줄을 서다",
            "explanation": (
                "Koreans are known for their dedicated queuing culture (줄서기 문화). "
                "A long queue is often a social signal of quality—if locals are lining up "
                "for hours, the food must be worth it. Cutting in line (새치기) is considered "
                "very rude."
            ),
        },
        {
            "id": "culture-3-3",
            "subtitleId": "s3-12",
            "title": "한국 인심 – Korean generosity",
            "keyword": "인심",
            "explanation": (
                "인심 (人心) literally means 'heart of the people' and refers to generosity "
                "or hospitality. Street vendors handing out free soup, shopkeepers offering "
                "small extras (서비스), and neighbors sharing food are classic expressions "
                "of 한국 인심."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# Lesson 4 – K-drama Vocabulary Basics
# ---------------------------------------------------------------------------
_SUBTITLES_4: dict[str, Any] = {
    "youtubeId": "dQw4w9WgXcQ",
    "durationSec": 390,
    "lines": [
        {
            "id": "s4-1",
            "startSec": 0,
            "endSec": 18,
            "korean": "안녕하세요! 오늘은 K-드라마 필수 단어를 배워볼게요.",
            "english": "Hello! Today we'll learn essential K-drama vocabulary.",
        },
        {
            "id": "s4-2",
            "startSec": 18,
            "endSec": 38,
            "korean": "8화의 반전은 모든 사람을 놀라게 했어요.",
            "english": "The plot twist in episode 8 surprised everyone.",
        },
        {
            "id": "s4-3",
            "startSec": 38,
            "endSec": 55,
            "korean": "마지막 반전에서 완전히 충격받았어요.",
            "english": "I was completely shocked by the final plot twist.",
        },
        {
            "id": "s4-4",
            "startSec": 55,
            "endSec": 72,
            "korean": "어젯밤에 한 시즌을 통째로 몰아봤어요.",
            "english": "I binge-watched an entire season last night.",
        },
        {
            "id": "s4-5",
            "startSec": 72,
            "endSec": 90,
            "korean": "요즘 드라마는 정말 빠져들게 만들어요.",
            "english": "These days dramas are really made to draw you in.",
        },
        {
            "id": "s4-6",
            "startSec": 90,
            "endSec": 108,
            "korean": "그 장면을 볼 때마다 가슴이 설레요.",
            "english": "My heart flutters every time I watch that scene.",
        },
        {
            "id": "s4-7",
            "startSec": 108,
            "endSec": 125,
            "korean": "로맨스 장면에서 설레는 감정을 잘 표현하는 단어예요.",
            "english": "It's a word that captures the fluttering emotion in romance scenes.",
        },
        {
            "id": "s4-8",
            "startSec": 125,
            "endSec": 140,
            "korean": "이 드라마 주인공은 정말 매력적이에요.",
            "english": "The main character of this drama is really charming.",
        },
        {
            "id": "s4-9",
            "startSec": 140,
            "endSec": 162,
            "korean": "주인공 말고도 조연들도 캐릭터가 살아있어요.",
            "english": "Not just the protagonist—the supporting characters are vivid too.",
        },
    ],
    "vocabMap": {
        "반전": {
            "meaning": "Plot twist / reversal",
            "cardId": "fc-4-1",
            "lessonId": "4",
            "expression": "반전",
            "exampleSentence": "8화의 반전은 모든 사람을 놀라게 했어요.",
            "exampleTranslation": "The plot twist in episode 8 surprised everyone.",
        },
        "몰아봤어요": {
            "meaning": "To binge-watch",
            "cardId": "fc-4-2",
            "lessonId": "4",
            "expression": "몰아봤어요",
            "exampleSentence": "어젯밤에 한 시즌을 통째로 몰아봤어요.",
            "exampleTranslation": "I binge-watched an entire season last night.",
        },
        "설레요": {
            "meaning": "To feel excited / flutter with anticipation",
            "cardId": "fc-4-3",
            "lessonId": "4",
            "expression": "설레요",
            "exampleSentence": "그 장면을 볼 때마다 가슴이 설레요.",
            "exampleTranslation": "My heart flutters every time I watch that scene.",
        },
        "주인공": {
            "meaning": "Main character / protagonist",
            "cardId": "fc-4-4",
            "lessonId": "4",
            "expression": "주인공",
            "exampleSentence": "이 드라마 주인공은 정말 매력적이에요.",
            "exampleTranslation": "The main character of this drama is really charming.",
        },
    },
    "culturalNotes": [
        {
            "id": "culture-4-1",
            "subtitleId": "s4-3",
            "title": "충격받다 – Expressing shock in Korean drama",
            "keyword": "충격",
            "explanation": (
                "충격받다 (to be shocked) is the natural way Koreans describe unexpected "
                "story turns. Unlike English where 'surprised' can be mild, 충격 implies "
                "a strong, unsettling impact—closer to 'blow' or 'bombshell'."
            ),
        },
        {
            "id": "culture-4-2",
            "subtitleId": "s4-6",
            "title": "설레다 – The untranslatable flutter",
            "keyword": "설레다",
            "explanation": (
                "설레다 describes the warm, excited flutter in your chest before something "
                "good—a first date, a trip, a love confession. Korean has no single English "
                "equivalent. Context determines whether it's anticipation, nervousness, or "
                "romantic excitement."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# Lesson 5 – Learn Korean with BLACKPINK
# ---------------------------------------------------------------------------
_SUBTITLES_5: dict[str, Any] = {
    "youtubeId": "dQw4w9WgXcQ",
    "durationSec": 300,
    "lines": [
        {
            "id": "s5-1",
            "startSec": 0,
            "endSec": 8,
            "korean": "오늘은 블랙핑크 노래로 한국어를 배워볼게요!",
            "english": "Today we'll learn Korean with BLACKPINK songs!",
        },
        {
            "id": "s5-2",
            "startSec": 8,
            "endSec": 24,
            "korean": "그들의 무대에서는 자신감이 넘쳐 흘러요.",
            "english": "Their stage performance overflows with confidence.",
        },
        {
            "id": "s5-3",
            "startSec": 24,
            "endSec": 40,
            "korean": "자신감 있는 태도가 그들의 매력 포인트예요.",
            "english": "Their confident attitude is their charm point.",
        },
        {
            "id": "s5-4",
            "startSec": 40,
            "endSec": 56,
            "korean": "이 노래 후렴구가 너무 중독성 있어서 계속 흥얼거리게 돼요.",
            "english": "The chorus is so addictive I keep humming it all day.",
        },
        {
            "id": "s5-5",
            "startSec": 56,
            "endSec": 78,
            "korean": "중독성 있는 멜로디는 팬들이 가장 좋아하는 부분이에요.",
            "english": "The addictive melody is the part fans love the most.",
        },
        {
            "id": "s5-6",
            "startSec": 78,
            "endSec": 100,
            "korean": "가사를 통해 배우는 한국어는 더 기억에 남아요.",
            "english": "Korean learned through lyrics stays in memory longer.",
        },
    ],
    "vocabMap": {
        "자신감": {
            "meaning": "Confidence / self-confidence",
            "cardId": "fc-5-1",
            "lessonId": "5",
            "expression": "자신감",
            "exampleSentence": "그들의 무대에서는 자신감이 넘쳐 흘러요.",
            "exampleTranslation": "Their stage performance overflows with confidence.",
        },
        "중독성 있어서": {
            "meaning": "Because it's addictive",
            "cardId": "fc-5-2",
            "lessonId": "5",
            "expression": "중독성 있어서",
            "exampleSentence": "이 노래 후렴구가 너무 중독성 있어서 계속 흥얼거리게 돼요.",
            "exampleTranslation": "The chorus is so addictive I keep humming it all day.",
        },
    },
    "culturalNotes": [
        {
            "id": "culture-5-1",
            "subtitleId": "s5-4",
            "title": "중독성 – The K-pop 'addiction' language",
            "keyword": "중독성",
            "explanation": (
                "중독성 있다 (to be addictive) is one of the most common compliments in "
                "K-pop fan culture. Fans use it to describe a hook that gets stuck in "
                "your head. The grammar point 있어서 = 'because it has', showing cause."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# Public registry
# ---------------------------------------------------------------------------
SUBTITLE_FIXTURES: dict[str, dict[str, Any]] = {
    "3": _SUBTITLES_3,
    "4": _SUBTITLES_4,
    "5": _SUBTITLES_5,
}


def get_public_subtitles(lesson_id: str) -> dict[str, Any] | None:
    return SUBTITLE_FIXTURES.get(lesson_id)
