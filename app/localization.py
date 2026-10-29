"""Conservative hand-reviewed Hindi, Bengali and Hinglish food-name aliases.

No automatic translation of uncertain dishes into unrelated catalogue IDs.
"""
import unicodedata

ALIASES={
    'चावल':'steamed-rice','chawal':'steamed-rice','bhaat':'steamed-rice','ভাত':'steamed-rice',
    'সাদা ভাত':'steamed-rice','सादा चावल':'steamed-rice',
    'दाल तड़का':'dal-tadka','daal tadka':'dal-tadka','डाल':'dal-tadka',
    'dosai':'dosa-plain',
    'इडली':'idli','ইডলি':'idli','idly':'idli',
    'माछेर झोल':'machher-jhol','মাছের ঝোল':'machher-jhol','macher jhol':'machher-jhol',
    'आलू दम':'aloo-dum','আলুর দম':'aloo-dum','aloor dum':'aloo-dum',
    'खिचड़ी':'khichdi','খিচুড়ি':'khichdi','khichuri':'khichdi',
    'রুটি':'roti','रोटी':'roti','rooti':'roti',
    'पोहे':'poha','পোহা':'poha',
    # A biryani label does not establish meat/veg variant. See ambiguous aliases below.
    'চোলার ডাল':'cholar-dal','ছোলার ডাল':'cholar-dal','cholar daal':'cholar-dal',
    'पनीर टिक्का':'paneer-tikka','পনির টিক্কা':'paneer-tikka',
    'আলু পোস্ত':'aloo-posto','aloo posto':'aloo-posto',
}

def alias_match(query:str):
    from .catalog import LOOKUP
    q=unicodedata.normalize('NFKC',query).strip().casefold()
    slug=ALIASES.get(q)
    return LOOKUP.get(slug) if slug else None

AMBIGUOUS_ALIASES={'बिरयानी':'biryani','बिर्यानी':'biryani','বিরিয়ানি':'biryani',
                   'डोसा':'dosa','দোসা':'dosa'}

def ambiguous_search_term(query:str):
    return AMBIGUOUS_ALIASES.get(unicodedata.normalize('NFKC',query).strip().casefold())
