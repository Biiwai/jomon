from collections import OrderedDict

curatorsSchema = OrderedDict([
    ("curatorId", "integer primary key"),	# First column is *always* primary key
    ("name", "text"),
    ("desc", "text"),
    ("avatar_url", "text"),
    ("page_url", "text"),
    ("num_followers", "integer")
])

recommendationsSchema = OrderedDict([
    ("reviewId", "integer primary key"),
    ("curatorId", "integer"),
    ("appId", "integer"),
    ("desc", "text"),
#    ("comments", "integer"), # Unused?
#    ("likes", "integer"), # Unused?
#    ("price", "text"),
    ("readmore", "text"),
])

appsSchema = OrderedDict([
    ("appId", "integer primary key"),
    ("name", "text"),
    ("about_the_game", "text"),
    ("detailed_description", "text"),
    ("background", "text"),
    ("header_image", "text"),
    ("isfree", "boolean"),
    ("metacritic_score", "integer"),
    ("metacritic_url", "text"),
    ("publishers", "text"),
    ("recommendations", "integer"),
    ("coming soon", "boolean"),
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
