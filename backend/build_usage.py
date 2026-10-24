"""
Adds a farmer-friendly `usage` block to every breed in breed_info.json.

Run once from the backend folder:   python build_usage.py
It is safe to re-run (it rewrites the `usage` block each time).

IMPORTANT: this is general breed guidance written from commonly published breed
descriptions. It is NOT official data. Verify the entries (especially the ones with
source_confidence = "check") against the ICAR-NBAGR breed registry before you
present them as fact.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
INFO = HERE / "breed_info.json"

# ---------------------------------------------------------------- text blocks
MILK = {
    "high": ("Good milk producer - a suitable choice if your main goal is milk.",
             "चांगले दूध देणारी जात - दूध हा मुख्य उद्देश असेल तर योग्य निवड."),
    "medium": ("Gives a moderate amount of milk - fine for a family and some sale, "
               "but not a commercial dairy breed.",
               "मध्यम प्रमाणात दूध देते - घरगुती वापर व थोड्या विक्रीसाठी पुरेसे, पण व्यावसायिक डेअरी जात नाही."),
    "low": ("Gives little milk - not a good choice if milk is your main goal.",
            "दूध कमी देते - दूध हा मुख्य उद्देश असेल तर योग्य नाही."),
    "very_low": ("Gives very little milk - kept mainly for other reasons.",
                 "दूध खूप कमी देते - मुख्यतः इतर कारणांसाठी पाळली जाते."),
    "unknown": ("Milk yield not confirmed for this breed.",
                "या जातीचे दूध उत्पादन निश्चित नाही."),
}
MILK_CROSS = ("High milk yield, more than most Indian breeds - but needs good feed, clean "
              "water, shade and regular vet care.",
              "जास्त दूध देते, बहुतेक भारतीय जातींपेक्षा जास्त - पण चांगला चारा, स्वच्छ पाणी, सावली व नियमित पशुवैद्यकीय काळजी आवश्यक.")

FARM = {
    "high": ("Strong bullocks - well suited to ploughing, carting and other farm work.",
             "ताकदवान बैल - नांगरणी, गाडी ओढणे व इतर शेतीकामांसाठी उत्तम."),
    "medium": ("Bullocks can do ploughing and carting - moderately strong.",
               "बैल नांगरणी व गाडी ओढण्याचे काम करू शकतात - मध्यम ताकद."),
    "low": ("Not suited to heavy farm work.",
            "जड शेतीकामांसाठी योग्य नाही."),
    "very_low": ("Not used for farm work.",
                 "शेतीकामासाठी वापरली जात नाही."),
    "unknown": ("Farm-work ability not confirmed.",
                "शेतीकामाची क्षमता निश्चित नाही."),
}
FARM_BUFFALO_LOW = ("Mainly kept for milk. Male buffaloes can do slow, heavy jobs, but they are "
                    "not the first choice for field work.",
                    "प्रामुख्याने दुधासाठी पाळली जाते. नर रेडे हळू पण जड कामे करू शकतात, पण शेतीकामासाठी पहिली निवड नाही.")

PURPOSE = {
    "dairy": ("MILK", "दूध उत्पादन"),
    "draught": ("FARM WORK (ploughing, carting)", "शेतीकाम (नांगरणी, गाडी ओढणे)"),
    "dual": ("MILK + FARM WORK (dual purpose)", "दूध + शेतीकाम (दुहेरी उपयोग)"),
    "crossbred_dairy": ("HIGH MILK (needs good care)", "जास्त दूध (चांगली काळजी आवश्यक)"),
    "small_dairy": ("small-scale / backyard keeping, low milk", "लहान प्रमाणात / अंगणातील पालन, कमी दूध"),
    "hill": ("hill farming - hardy, low milk, light work", "डोंगराळ भागातील शेती - काटक, कमी दूध, हलकी कामे"),
    "wetland_draught": ("FARM WORK in wet paddy land", "ओल्या भातशेतीतील शेतीकाम"),
    "unknown": ("Details not confirmed", "तपशील निश्चित नाहीत"),
}

NOTE = ("General guidance for the breed - individual animals vary. "
        "Confirm with your local veterinary officer.",
        "ही जातीसाठी सर्वसाधारण माहिती आहे - प्रत्येक जनावर वेगळे असते. स्थानिक पशुवैद्यकीय अधिकाऱ्यांकडून खात्री करा.")

# ---------------------------------------------------- per-breed data
# name: (primary_use, milk_level, farm_level, confidence)
B = {}
def add(names, use, milk, farm, conf="general"):
    for n in names.split():
        B[n] = (use, milk, farm, conf)

# Indigenous dairy cattle
add("Gir Sahiwal Red_Sindhi Rathi", "dairy", "high", "low")
# Dual-purpose cattle
add("Deoni Hariana Kankrej Mewati Nari Tharparkar Gangatiri", "dual", "medium", "high")
add("Gaolao Nimari Ongole", "dual", "low", "high")
# Draught cattle
add("Alambadi Amritmahal Bargur Dangi Hallikar Kangayam Kenkatha Kherigarh Khillari "
    "Krishna_Valley Malvi Nagori Ponwar Pulikulam Red_Kandhari", "draught", "low", "high")
add("Umblachery", "wetland_draught", "low", "high")
# Local / lesser-documented cattle -> check against NBAGR
add("Bachaur Ghumsari Khariar Kosali Poda_Thirupu Purnea Lakhimi Konkan_Kapila Shweta_Kapila Thutho",
    "dual", "low", "medium", "check")
# Hill cattle
add("Badri Himachali_Pahari Ladakhi Siri", "hill", "low", "medium")
# Small / dwarf cattle
add("Kasargod Malnad_Gidda Punganur Vechur", "small_dairy", "low", "very_low")
# Crossbred cattle
add("Ayrshire_Cross Brown_Swiss_Cross Guernsey_Cross HF_Cross Jersey_Cross Red_Dane_Cross",
    "crossbred_dairy", "high", "very_low")
# Buffalo
add("Murrah Banni Jaffarabadi Mehsana Nili_Ravi", "dairy", "high", "low")
add("Surti Pandharpuri Bhadawari Gojri", "dairy", "medium", "low")
add("Marathwadi Nagpuri Chilika", "dual", "medium", "medium")
add("Chhattisgarhi Kalahandi", "dual", "low", "medium")
add("Luit", "wetland_draught", "very_low", "medium")
add("Toda", "unknown", "low", "low", "check")
# Unconfirmed breeds
add("Bhelai Dagri Motu", "unknown", "unknown", "unknown", "check")
B["Jaffarabadi"] = ("dairy", "high", "medium", "general")
B["Gojri"] = ("dairy", "medium", "low", "check")

# ------------------------------------------- specific "where to use" lines (en, mr)
WHERE = {
    "Khillari": ("Fast, hardy bullocks for ploughing and carting on dry, rocky land and black cotton soil (Maharashtra/Karnataka dry belt).",
                 "कोरड्या, खडकाळ जमिनीवर व काळ्या कापसाच्या जमिनीत नांगरणी व गाडी ओढण्यासाठी वेगवान, काटक बैल (महाराष्ट्र/कर्नाटकचा कोरडा पट्टा)."),
    "Dangi": ("Suited to heavy-rainfall hilly areas - good for ploughing rice (paddy) fields (Nashik, Ahmednagar, Thane belt).",
              "जास्त पावसाच्या डोंगराळ भागात योग्य - भातशेतीतील नांगरणीसाठी चांगले (नाशिक, अहमदनगर, ठाणे पट्टा)."),
    "Kangayam": ("Strong bullocks for ploughing and carting on dry land in Tamil Nadu.",
                 "तमिळनाडूतील कोरड्या जमिनीवर नांगरणी व गाडी ओढण्यासाठी ताकदवान बैल."),
    "Hallikar": ("Fast trotting bullocks for ploughing and carting on dry red soils of Karnataka.",
                 "कर्नाटकातील कोरड्या लाल जमिनीवर नांगरणी व गाडी ओढण्यासाठी वेगवान बैल."),
    "Amritmahal": ("Fast, strong bullocks for ploughing and transport on dry land (Karnataka).",
                   "कोरड्या जमिनीवर नांगरणी व वाहतुकीसाठी वेगवान, ताकदवान बैल (कर्नाटक)."),
    "Alambadi": ("Hardy bullocks for ploughing and carting on hilly, forest-edge land (Tamil Nadu).",
                 "डोंगराळ, जंगलाजवळच्या जमिनीवर नांगरणी व गाडी ओढण्यासाठी काटक बैल (तमिळनाडू)."),
    "Bargur": ("Fast bullocks for ploughing and transport in hill tracts (Tamil Nadu).",
               "डोंगराळ भागात नांगरणी व वाहतुकीसाठी वेगवान बैल (तमिळनाडू)."),
    "Umblachery": ("Used for ploughing in wet, puddled paddy fields of the Tamil Nadu delta.",
                   "तमिळनाडूच्या डेल्टा भागातील ओल्या, चिखलाच्या भातशेतीत नांगरणीसाठी वापरली जाते."),
    "Pulikulam": ("Ploughing and light carting on dry land (Tamil Nadu).",
                  "कोरड्या जमिनीवर नांगरणी व हलकी गाडी ओढणे (तमिळनाडू)."),
    "Nagori": ("Fast trotting bullocks for ploughing and carting on sandy soil (Rajasthan).",
               "वाळूमय जमिनीवर नांगरणी व गाडी ओढण्यासाठी वेगवान बैल (राजस्थान)."),
    "Kherigarh": ("Fast bullocks for light carting and field work (Uttar Pradesh).",
                  "हलकी गाडी ओढणे व शेतीकामासाठी वेगवान बैल (उत्तर प्रदेश)."),
    "Ponwar": ("Ploughing and light carting (Uttar Pradesh).",
               "नांगरणी व हलकी गाडी ओढणे (उत्तर प्रदेश)."),
    "Kenkatha": ("Small, hardy bullocks for ploughing on rocky, uneven land (Bundelkhand).",
                 "खडकाळ, असमान जमिनीवर नांगरणीसाठी लहान, काटक बैल (बुंदेलखंड)."),
    "Malvi": ("Ploughing and carting on the black soils of the Malwa plateau (Madhya Pradesh).",
              "माळवा पठारावरील काळ्या जमिनीत नांगरणी व गाडी ओढणे (मध्य प्रदेश)."),
    "Krishna_Valley": ("Heavy ploughing and carting in black cotton soil (Krishna valley, Karnataka/Maharashtra).",
                       "काळ्या कापसाच्या जमिनीत जड नांगरणी व गाडी ओढणे (कृष्णा खोरे, कर्नाटक/महाराष्ट्र)."),
    "Red_Kandhari": ("Ploughing and carting in Maharashtra (Nanded/Latur region).",
                     "महाराष्ट्रात (नांदेड/लातूर भाग) नांगरणी व गाडी ओढणे."),
    "Ongole": ("Heavy bullocks for ploughing and pulling heavy carts (Andhra Pradesh).",
               "नांगरणी व जड गाड्या ओढण्यासाठी मोठे बैल (आंध्र प्रदेश)."),
    "Kankrej": ("Strong, fast bullocks for ploughing and carting (Gujarat/Rajasthan); cows give fair milk too.",
                "नांगरणी व गाडी ओढण्यासाठी ताकदवान, वेगवान बैल (गुजरात/राजस्थान); गायी बऱ्यापैकी दूधही देतात."),
    "Hariana": ("Bullocks used for ploughing and carting on light soils (Haryana/Punjab); cows give fair milk.",
                "हलक्या जमिनीवर नांगरणी व गाडी ओढण्यासाठी बैल (हरियाणा/पंजाब); गायी बऱ्यापैकी दूध देतात."),
    "Deoni": ("Bullocks suited to ploughing in the heavy black soils of Marathwada/North Karnataka; cows give moderate milk.",
              "मराठवाडा/उत्तर कर्नाटकच्या जड काळ्या जमिनीत नांगरणीसाठी योग्य बैल; गायी मध्यम दूध देतात."),
    "Gaolao": ("Ploughing and carting in the Wardha/Nagpur belt; cows give little milk.",
               "वर्धा/नागपूर पट्ट्यात नांगरणी व गाडी ओढणे; गायी कमी दूध देतात."),
    "Tharparkar": ("Cows give good milk in hot, dry areas; bullocks do farm work (Rajasthan, drought-hardy).",
                   "उष्ण, कोरड्या भागात गायी चांगले दूध देतात; बैल शेतीकाम करतात (राजस्थान, दुष्काळ सहनशील)."),
    "Mewati": ("Strong bullocks for heavy farm work (Rajasthan/Haryana); cows give fair milk.",
               "जड शेतीकामासाठी ताकदवान बैल (राजस्थान/हरियाणा); गायी बऱ्यापैकी दूध देतात."),
    "Nari": ("Cows give fair milk and bullocks do farm work (Rajasthan/Gujarat).",
             "गायी बऱ्यापैकी दूध देतात व बैल शेतीकाम करतात (राजस्थान/गुजरात)."),
    "Nimari": ("Ploughing and carting on the Nimar plains (Madhya Pradesh); cows give little milk.",
               "निमार मैदानात नांगरणी व गाडी ओढणे (मध्य प्रदेश); गायी कमी दूध देतात."),
    "Gir": ("Heat-tolerant milk breed (Gujarat); bullocks are not used much for farm work.",
            "उष्णता सहन करणारी दुभती जात (गुजरात); बैल शेतीकामासाठी फारसे वापरले जात नाहीत."),
    "Sahiwal": ("Heat- and tick-tolerant milk breed (Punjab); suits hot climates.",
                "उष्णता व गोचीड सहन करणारी दुभती जात (पंजाब); उष्ण हवामानासाठी योग्य."),
    "Jaffarabadi": ("Very heavy buffalo; males can pull heavy loads, but females are kept mainly for milk with high fat.",
                    "खूप मोठी म्हैस; नर जड ओझी ओढू शकतात, पण माद्या प्रामुख्याने जास्त फॅटच्या दुधासाठी पाळल्या जातात."),
    "Luit": ("Swamp-type buffalo used for work in wet, marshy paddy land (Assam).",
             "दलदलीच्या भातशेतीत कामासाठी वापरली जाणारी दलदल प्रकारची म्हैस (आसाम)."),
    "Nagpuri": ("Females give moderate milk; males are used for slow draught work (Vidarbha).",
                "माद्या मध्यम दूध देतात; नर हळू ओढकामासाठी वापरले जातात (विदर्भ)."),
}

# extra short tips (en, mr)
TIP = {
    "Murrah": ("Top milk buffalo in India; milk fat about 7%. Needs good green fodder and water.",
               "भारतातील सर्वाधिक दूध देणारी म्हैस; दुधातील फॅट सुमारे ७%. चांगला हिरवा चारा व पाणी आवश्यक."),
    "Bhadawari": ("Gives less milk, but very high fat - good for ghee/butter.",
                  "दूध कमी, पण फॅट खूप जास्त - तूप/लोणीसाठी चांगली."),
    "Surti": ("Medium-sized buffalo with high-fat milk.",
              "मध्यम आकाराची म्हैस; जास्त फॅटचे दूध."),
    "Jaffarabadi": ("Milk fat is high (about 8%); needs plenty of feed because of its size.",
                    "दुधातील फॅट जास्त (सुमारे ८%); मोठ्या आकारामुळे भरपूर चारा लागतो."),
    "HF_Cross": ("Holstein Friesian crosses give the most milk, but suffer in heat - provide shade and water.",
                 "होल्स्टिन फ्रिजियन संकरित गायी सर्वाधिक दूध देतात, पण उष्णतेचा त्रास होतो - सावली व पाणी द्या."),
    "Jersey_Cross": ("Jersey crosses are smaller, tolerate heat better than HF crosses and give rich milk.",
                     "जर्सी संकरित गायी लहान असतात, HF पेक्षा उष्णता चांगली सहन करतात व दूध घट्ट देतात."),
    "Gir": ("Good for small dairy farms in hot areas.", "उष्ण भागातील लहान डेअरी शेतांसाठी चांगली."),
    "Vechur": ("Tiny cow; low milk but needs very little feed.", "लहान गाय; दूध कमी, पण चारा खूप कमी लागतो."),
    "Kasargod": ("Tiny hardy cow; low milk, very low feed need.", "लहान काटक गाय; दूध कमी, चारा खूप कमी लागतो."),
    "Punganur": ("Tiny cow; low milk quantity but rich milk.", "लहान गाय; दूध कमी पण घट्ट."),
}

# approximate lactation yield in kg (low, high) - ONLY for breeds with well-known figures
APPROX_MILK_KG = {
    "Murrah": (1800, 2200),
    "Gir": (1200, 1800),
    "Sahiwal": (1800, 2500),
    "HF_Cross": (3000, 4500),
}


def build(name, info):
    use, milk, farm, conf = B[name]
    t = info.get("type")
    is_buffalo = t == "buffalo"
    is_cross = use == "crossbred_dairy"

    milk_en, milk_mr = MILK_CROSS if is_cross else MILK[milk]
    if is_buffalo and farm in ("low", "very_low") and use == "dairy":
        farm_en, farm_mr = FARM_BUFFALO_LOW
    else:
        farm_en, farm_mr = FARM[farm]
    where = WHERE.get(name)
    if where:
        farm_en, farm_mr = where
    if use == "unknown" or conf == "check" and use == "unknown":
        conf = "check"

    usage = {
        "primary_use": use,
        "purpose_en": PURPOSE[use][0],
        "purpose_mr": PURPOSE[use][1],
        "milk_level": milk,
        "farm_work_level": farm,
        "milk_en": milk_en, "milk_mr": milk_mr,
        "farm_en": farm_en, "farm_mr": farm_mr,
        "source_confidence": conf,
        "note_en": NOTE[0], "note_mr": NOTE[1],
    }
    if name in TIP:
        usage["tip_en"], usage["tip_mr"] = TIP[name]
    if name in APPROX_MILK_KG:
        lo, hi = APPROX_MILK_KG[name]
        usage["approx_milk_kg_per_lactation"] = [lo, hi]
    return usage


def main():
    data = json.loads(INFO.read_text(encoding="utf-8"))
    missing = [n for n in data if n not in B]
    extra = [n for n in B if n not in data]
    assert not missing and not extra, f"missing={missing} extra={extra}"
    for name, info in data.items():
        info["usage"] = build(name, info)
    INFO.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated {len(data)} breeds in {INFO.name}")


if __name__ == "__main__":
    main()
