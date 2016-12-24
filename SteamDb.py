from collections import OrderedDict

curatorSchema = OrderedDict([
    ("curator_id", "integer primary key"),	# First column is *always* primary key
    ("name", "text"),
    ("desc", "text"),
    ("avatar_url", "text"),
    ("page_url", "text"),
    ("num_followers", "integer")
])

recommendationSchema = OrderedDict([
    ("review_id", "integer primary key"),
    ("curator_id", "integer"),
    ("app_id", "integer"),
    ("desc", "text"),
#    ("comments", "integer"), # Unused?
#    ("likes", "integer"), # Unused?
#    ("price", "text"),
    ("readmore", "text"),
])

appSchema = OrderedDict([
    ("app_id", "integer primary key"),
    ("name", "text"),
    ("about_the_game", "text"),
    ("detailed_description", "text"),
    ("background", "text"),
    ("header_image", "text"),
    ("is_free", "boolean"),
    ("metacritic_score", "integer"),
    ("metacritic_url", "text"),
    ("publishers", "text"),
    ("num_recommendations", "integer"),
    ("coming_soon", "boolean"),
    ("release_date", "text"),
    ("required_age", "integer"),
    ("support_url", "text"),
    ("type", "text"),
    ("website", "text")
#    ("pc_requirements", "text"),
#    ("mac_requirements", "text"),
#    ("linux_requirements", "text"),
#categories
#genres
#platforms
#price_overview
#screenshots
])

