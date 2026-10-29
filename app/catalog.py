"""Indicative starter catalogue; NOT a verified nutritional or camera dataset.

Per-100 g for solids; per-100 ml for Drinks/Mocktails (legacy field names remain).
"""
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP
import math
import re
import csv
import os
from pathlib import Path

# Illustrative per-100-unit values (g solid / ml drinks); variability can be large. Replace with approved
# IFCT / INDB / FDC data before any real dietary or clinical use.
# name | kcal | protein | carbohydrate | fat | typical grams | category | aliases
ROWS = '''
Roti|300|9|50|7|40|North Indian|chapati,phulka
Naan|291|9|50|6|90|North Indian|naan bread
Paratha|326|8|42|14|85|North Indian|plain paratha
Aloo Paratha|255|6|34|10|130|North Indian|potato paratha
Paneer Paratha|279|11|34|12|140|North Indian|
Puri|340|6|41|17|45|North Indian|poori
Bhatura|340|8|45|15|100|North Indian|
Dal Tadka|115|6|14|4|200|North Indian|dal fry,dahl
Dal Makhani|160|7|15|8|200|North Indian|
Chole|150|7|21|5|200|North Indian|chana masala,chickpea curry
Rajma Curry|120|7|19|2|200|North Indian|kidney bean curry
Paneer Butter Masala|235|11|9|17|200|North Indian|paneer makhani
Palak Paneer|180|10|7|12|200|North Indian|saag paneer
Shahi Paneer|250|11|10|19|180|North Indian|
Kadai Paneer|190|12|9|13|180|North Indian|
Paneer Tikka|185|18|7|10|150|North Indian|
Butter Chicken|190|16|6|11|220|North Indian|murgh makhani
Chicken Tikka|155|24|3|5|170|North Indian|
Chicken Curry|175|17|5|10|220|North Indian|
Mutton Curry|220|17|4|15|220|North Indian|goat curry
Kofta Curry|200|8|12|13|200|North Indian|
Aloo Gobi|125|3|14|6|180|North Indian|potato cauliflower
Bhindi Masala|115|3|10|8|160|North Indian|okra curry
Baingan Bharta|115|2|9|8|180|North Indian|eggplant mash
Mixed Veg Curry|105|3|12|5|200|North Indian|
Jeera Rice|155|3|30|3|190|North Indian|cumin rice
Steamed Rice|130|2.7|28|0.3|200|Staples|white rice,plain rice,rice
Brown Rice Cooked|112|2.6|23|0.9|200|Staples|brown rice
Khichdi|125|4|22|2.5|250|Staples|khichuri
Rajma Chawal|145|6|27|2|300|North Indian|
Chole Bhature|260|8|32|11|300|North Indian|
Biryani Chicken|170|9|23|5|300|Rice & Biryani|chicken biryani
Biryani Veg|145|3.5|24|4|300|Rice & Biryani|veg biryani,vegetable biryani
Biryani Mutton|185|9|22|7|300|Rice & Biryani|mutton biryani
Pulao Veg|145|3|26|3.5|250|Rice & Biryani|veg pulao
Pulao Peas|150|4|27|3.5|250|Rice & Biryani|matar pulao
Curd Rice|135|4|22|4|250|South Indian|thayir sadam
Lemon Rice|165|3|29|4|250|South Indian|chitranna
Tamarind Rice|180|4|31|5|250|South Indian|puliyogare
Coconut Rice|195|3.5|30|7|250|South Indian|
Tomato Rice|155|3|27|4|250|South Indian|
Idli|145|4.5|30|0.5|80|South Indian|idly
Sambar|70|3.5|11|1.5|180|South Indian|sambhar
Dosa Plain|185|4|28|6|100|South Indian|plain dosa
Masala Dosa|215|5|30|8|180|South Indian|
Rava Dosa|225|4|32|9|130|South Indian|
Onion Dosa|210|5|29|8|130|South Indian|
Mysore Masala Dosa|220|5|30|9|180|South Indian|
Uttapam|190|5|29|6|180|South Indian|uthappam
Onion Uttapam|185|5|28|6|180|South Indian|
Medu Vada|310|10|35|15|70|South Indian|vada,ulundu vadai
Upma|125|3|22|3|200|South Indian|rava upma
Pongal|175|5|29|5|220|South Indian|ven pongal
Pesarattu|175|9|25|4|150|South Indian|green gram dosa
Appam|165|3|32|3|100|South Indian|
Idiyappam|155|3|32|1|150|South Indian|string hoppers
Puttu|175|4|36|2|150|South Indian|
Kadala Curry|150|7|22|4|180|South Indian|
Avial|115|3|12|6|180|South Indian|
Rasam|35|1|6|0.5|180|South Indian|
Coconut Chutney|240|3|10|21|40|South Indian|
Tomato Chutney|100|2|12|5|40|South Indian|
Peanut Chutney|265|10|13|21|40|South Indian|
Fish Curry Kerala|160|15|5|9|200|South Indian|
Chicken Chettinad|215|18|5|13|200|South Indian|
Hyderabadi Biryani|185|9|24|6|300|South Indian|
Poha|135|3|26|2.5|200|West Indian|flattened rice
Kanda Poha|145|3|27|3.5|200|West Indian|
Sabudana Khichdi|235|3|39|8|200|West Indian|
Misal Pav|195|7|26|7|250|West Indian|
Pav Bhaji|175|5|27|6|250|West Indian|
Vada Pav|270|5|40|10|150|West Indian|
Dabeli|250|5|36|9|150|West Indian|
Dhokla|165|7|24|5|120|West Indian|
Khandvi|155|6|16|8|120|West Indian|
Thepla|300|8|42|11|80|West Indian|
Undhiyu|145|4|17|7|200|West Indian|
Fish Fry|230|21|12|11|150|East Indian|
Machher Jhol|130|16|5|6|200|East Indian|macher jhol,fish curry bengali
Shorshe Ilish|245|17|6|17|180|East Indian|hilsa mustard curry
Chingri Malai Curry|200|17|8|11|180|East Indian|prawn malai curry
Luchi|355|6|42|18|45|East Indian|
Aloo Dum|145|3|20|6|180|East Indian|dum aloo
Shukto|95|2|14|3|180|East Indian|
Cholar Dal|135|6|19|4|200|East Indian|
Ghugni|130|6|20|3|200|East Indian|
Momos Veg|180|6|29|5|150|Snacks|veg momos
Momos Chicken|195|11|26|5|150|Snacks|chicken momos
Samosa|265|5|32|13|100|Snacks|
Pakora|290|7|30|16|100|Snacks|pakode,pakoda
Aloo Tikki|210|3|30|9|120|Snacks|
Pani Puri|210|4|38|5|100|Snacks|golgappa,puchka,phuchka
Bhel Puri|170|4|30|4|180|Snacks|
Sev Puri|235|5|32|10|150|Snacks|
Papdi Chaat|235|6|29|10|170|Snacks|
Dahi Vada|160|6|20|6|150|Snacks|
Kachori|330|7|39|16|100|Snacks|
Spring Roll|215|6|29|8|100|Snacks|spring rolls
Sandwich Veg|195|6|27|6|160|Snacks|vegetable sandwich
Grilled Cheese Sandwich|305|12|29|16|160|Snacks|
French Fries|310|3|41|15|120|Fast Food|fries
Burger Veg|235|7|33|8|200|Fast Food|vegetarian burger
Burger Chicken|245|14|28|9|200|Fast Food|
Pizza Margherita|255|11|32|9|200|Fast Food|cheese pizza,pizza
Pizza Paneer|270|13|31|10|200|Fast Food|
Pizza Pepperoni|285|12|31|12|200|Fast Food|
Pizza Veg Supreme|250|10|33|8|200|Fast Food|
Pasta Red Sauce|155|5.5|26|3.5|250|Italian|pasta arrabbiata
Pasta White Sauce|235|7|26|11|250|Italian|alfredo pasta,white sauce pasta
Pasta Pesto|225|7|26|10|250|Italian|
Mac and Cheese|245|10|28|11|250|Italian|macaroni cheese
Spaghetti Bolognese|165|9|21|5|250|Italian|
Lasagna|165|10|14|7|250|Italian|
Garlic Bread|350|9|42|16|80|Italian|
Fried Rice Veg|175|4|29|5|250|Asian|vegetable fried rice
Fried Rice Egg|180|6|28|5|250|Asian|egg fried rice
Hakka Noodles Veg|180|5|27|6|250|Asian|veg noodles
Hakka Noodles Chicken|195|10|25|6|250|Asian|
Manchurian Veg|190|5|22|9|200|Asian|
Chilli Chicken|210|17|13|10|200|Asian|
Chilli Paneer|240|13|12|15|200|Asian|
Chicken Chow Mein|190|10|25|6|250|Asian|
Boiled Egg|155|13|1|11|50|Protein|egg
Egg Omelette|170|12|2|12|100|Protein|omelet
Egg Bhurji|190|12|4|14|150|Protein|scrambled eggs
Chicken Breast Cooked|165|31|0|3.6|150|Protein|chicken breast
Paneer Plain|265|18|3|21|100|Protein|paneer,cottage cheese
Tofu Firm|144|15|3|8|100|Protein|tofu
Soy Chunks Cooked|115|16|8|1|100|Protein|soya chunks
Chickpeas Boiled|164|9|27|2.6|150|Protein|chana boiled
Moong Dal Cooked|105|7|18|0.5|180|Protein|mung dal
Red Lentils Cooked|116|9|20|0.4|180|Protein|masoor dal
Greek Yogurt|95|9|4|4|170|Protein|hung curd
Milk Whole|62|3.2|4.8|3.4|250|Drinks|milk
Lassi Sweet|110|3.5|16|3|250|Drinks|
Buttermilk|40|2|4|1.8|250|Drinks|chaas
Masala Chai|65|2|9|2.5|150|Drinks|chai,tea with milk
Black Coffee|2|0|0|0|200|Drinks|coffee
Cappuccino|60|3.5|5|3|180|Drinks|
Mango Shake|125|3|22|3|250|Drinks|
Sugarcane Juice|70|0|17|0|250|Drinks|
Orange Juice|45|0.7|10|0|250|Drinks|
Gulab Jamun|325|5|54|10|60|Desserts|
Rasgulla|185|5|39|1|60|Desserts|rosogolla
Sandesh|250|12|35|7|60|Desserts|
Rasmalai|195|8|24|8|100|Desserts|
Jalebi|370|2|69|10|80|Desserts|
Kheer Rice|155|4|23|5|150|Desserts|payasam
Gajar Halwa|250|4|29|14|140|Desserts|
Kulfi|230|6|27|11|85|Desserts|
Ice Cream Vanilla|210|3.5|24|11|100|Desserts|vanilla icecream
Chocolate Cake|370|5|50|17|100|Desserts|
Banana|89|1.1|23|0.3|120|Fruit|kela
Apple|52|0.3|14|0.2|160|Fruit|seb
Orange|47|0.9|12|0.1|140|Fruit|
Mango|60|0.8|15|0.4|150|Fruit|
Guava|68|2.6|14|1|120|Fruit|
Papaya|43|0.5|11|0.3|150|Fruit|
Watermelon|30|0.6|8|0.2|250|Fruit|
Dates|282|2.5|75|0.4|30|Fruit|khajoor
Almonds|579|21|22|50|30|Nuts|badam
Peanuts Roasted|585|24|21|50|30|Nuts|moongfali
Cashews|553|18|30|44|30|Nuts|kaju
Walnuts|654|15|14|65|30|Nuts|akhrot
Peanut Butter|588|25|20|50|32|Nuts|
Oats Cooked|68|2.4|12|1.4|230|Breakfast|porridge
Cornflakes Milk|110|3.5|18|2.5|220|Breakfast|
Bread White|265|9|49|3|60|Breakfast|bread
Bread Whole Wheat|250|12|42|4|60|Breakfast|brown bread
Peanut Butter Toast|335|12|36|16|90|Breakfast|
Protein Shake Whey Mixed Water|75|15|2|1|250|Protein|whey shake
Cola Regular Generic|42|0|10.6|0|330|Drinks|coca cola,coke,cola regular,soft drink cola
Cola Sugar Free Generic|0|0|0|0|330|Drinks|diet coke,coca cola zero,cola zero
Sausage Chicken Cooked Generic|215|15|3|16|100|Protein|chicken sausage,sausages
Sausage Pork Cooked Generic|300|12|3|27|100|Protein|pork sausages
Aloo Sabzi|120|2|18|5|170|North Indian|aloo curry,potato sabzi
Dal Chawal|128|5|23|2|300|North Indian|dal rice,dal bhaat
Boiled Potato|87|2|20|0.1|150|Staples|plain potato,aloo boiled
Sweet Corn Boiled|96|3.4|21|1.5|150|Staples|corn
Chicken Nuggets Generic|285|15|20|16|150|Fast Food|nuggets
Hot Dog Generic|260|11|24|13|180|Fast Food|hotdog
Soda Lemon Sugared Generic|40|0|10|0|250|Drinks|lemon soda
Energy Drink Generic|45|0|11|0|250|Drinks|energy drink
Whey Protein Powder Generic|380|75|9|6|30|Protein|protein powder,whey scoop
Greek Yogurt Plain Low Fat Generic|75|10|4|2|100|Protein|protein yoghurt,high protein yogurt
Paneer Wrap|215|10|27|8|180|Fast Food|paneer roll
Chicken Wrap|190|14|24|5|180|Fast Food|chicken roll
Pizza Farmhouse Generic|260|10|34|9|220|Fast Food|farmhouse pizza
Pasta Aglio Olio|190|5|28|6|250|Italian|spaghetti aglio olio
Cold Coffee Sweet|90|3|13|3|250|Drinks|iced coffee
Lemonade Sugared|42|0|10|0|250|Drinks|nimbu pani,sweet lemonade
Black Tea|1|0|0|0|150|Drinks|black tea
Soda Water|0|0|0|0|250|Drinks|sparkling water
Fried Rice Chicken|195|9|25|6|270|Asian|chicken fried rice
Fried Rice Prawn|185|8|26|5|270|Asian|prawn fried rice,shrimp fried rice
Fried Rice Paneer|195|8|25|7|270|Asian|paneer fried rice
Fried Rice Schezwan Veg|195|4|29|7|270|Asian|veg schezwan fried rice,schezwan rice
Fried Rice Schezwan Chicken|210|10|27|7|270|Asian|chicken schezwan fried rice
Fried Rice Mixed|200|9|26|6|270|Asian|mixed fried rice,combination fried rice
Fried Rice Garlic|185|4|29|6|260|Asian|garlic fried rice
Fried Rice Kimchi|155|5|23|5|250|Asian|kimchi rice
Fried Rice Triple Schezwan|220|9|29|8|320|Asian|triple schezwan rice
Chilli Garlic Noodles|210|6|30|8|250|Asian|chili garlic noodles
Singapore Noodles|180|7|28|5|250|Asian|singapore chowmein
Schezwan Noodles|210|7|30|7|250|Asian|schezwan chowmein
Chicken Lollipop|280|19|9|17|150|Asian|chicken lollipops
Crispy Chilli Baby Corn|185|4|27|7|180|Asian|baby corn chilli
Kolkata Chicken Biryani|185|9|25|6|320|Rice & Biryani|kolkata style biryani
Kolkata Mutton Biryani|195|10|24|7|320|Rice & Biryani|kolkata style mutton biryani
Egg Biryani|170|7|23|6|300|Rice & Biryani|anda biryani
Fish Biryani|165|9|23|4|300|Rice & Biryani|
Soya Biryani|175|9|24|5|300|Rice & Biryani|soy biryani
Tehri|165|4|28|4|280|Rice & Biryani|tahri
Ghee Rice|205|3|31|8|220|Rice & Biryani|
Chocolate Brownie|440|5|54|23|85|Desserts|brownie
Sizzling Brownie With Ice Cream|360|5|44|19|180|Desserts|sizzling brownie,brownie ice cream
New York Cheesecake|320|6|27|22|120|Desserts|cheesecake classic
Blueberry Cheesecake|315|6|32|19|120|Desserts|
Chocolate Cheesecake|350|6|32|22|120|Desserts|
Chocolate Mousse|255|4|26|16|110|Desserts|
Chocolate Lava Cake|390|6|45|21|110|Desserts|molten chocolate cake
Red Velvet Cake|370|5|47|19|120|Desserts|
Carrot Cake Frosted|365|4|48|18|120|Desserts|
Tiramisu|290|6|30|16|130|Desserts|
Waffle With Syrup|310|6|45|12|150|Desserts|waffles
Pancakes With Syrup|255|6|43|7|170|Desserts|
Glazed Donut|420|5|50|21|75|Desserts|doughnut
Ice Cream Sundae|250|4|30|12|180|Desserts|sundae
Gelato|195|4|25|9|120|Desserts|
Falooda|175|4|25|7|270|Desserts|faluda
Mishti Doi|155|5|20|6|150|Desserts|misti doi,sweet curd
Payesh Bengali|160|4|24|5|150|Desserts|bengali payesh
Rabri|225|7|26|11|120|Desserts|rabdi
Shahi Tukda|340|7|39|18|140|Desserts|shahi tukra
Malpua|315|6|42|14|120|Desserts|
Phirni|145|4|24|4|140|Desserts|
Shrikhand|290|7|42|11|120|Desserts|
Fruit Custard|125|3|21|3|170|Desserts|
Baklava|435|7|50|23|100|Desserts|
Churros|380|6|44|20|100|Desserts|
Virgin Mojito Sugared|47|0|11.5|0|300|Mocktails|mojito,virgin mojito,mint mojito
Virgin Mojito No Sugar|5|0|1|0|300|Mocktails|unsweetened mojito
Strawberry Mojito|60|0.1|14|0|300|Mocktails|strawberry mocktail
Blue Lagoon Mocktail|55|0|13.5|0|300|Mocktails|blue lagoon non alcoholic
Virgin Pina Colada|110|0.5|16|5|300|Mocktails|pina colada mocktail,non alcoholic pina colada
Fruit Punch Mocktail|65|0.4|15|0|300|Mocktails|fruit punch
Watermelon Cooler|35|0.5|8|0|300|Mocktails|watermelon mocktail
Mint Lemonade Mocktail|40|0|10|0|300|Mocktails|mint lime cooler
Mango Mocktail|82|0.5|19|0.2|300|Mocktails|mango cooler
Peach Iced Tea|38|0|9.5|0|300|Mocktails|peach tea iced
Lemon Iced Tea|34|0|8.5|0|300|Mocktails|iced tea lemon
Rose Lemonade|50|0|12|0|300|Mocktails|rose cooler
Jaljeera Drink|25|0.2|5|0|250|Mocktails|jaljeera,jaljira
Aam Panna Drink|65|0.1|16|0|250|Mocktails|aam panna
Cucumber Mint Cooler|22|0|5.5|0|300|Mocktails|cucumber cooler
Strawberry Milkshake|115|3|19|3|300|Drinks|strawberry shake
Chocolate Milkshake|125|3.5|19|4|300|Drinks|chocolate shake
Vanilla Milkshake|110|3|18|3|300|Drinks|vanilla shake
Oreo Milkshake|165|4|24|6|300|Drinks|oreo shake
Mango Smoothie|85|2|14|2.5|300|Drinks|mango smoothie
Banana Smoothie|100|3|16|3|300|Drinks|banana smoothie
Milk Tea Boba|110|1.5|22|2|350|Drinks|bubble tea,boba tea
Cold Coffee With Ice Cream|140|3|19|6|300|Drinks|cold coffee ice cream
Tender Coconut Water|19|0.7|3.7|0.2|250|Drinks|coconut water
Shawarma Chicken|235|13|22|10|200|Fast Food|chicken shawarma
Chicken Wings Fried|290|18|12|19|180|Fast Food|fried chicken wings
Cheese Nachos|315|9|32|17|180|Fast Food|loaded nachos
Tacos Chicken|205|12|23|7|190|Fast Food|chicken tacos
Kolkata Egg Roll|245|9|26|12|170|Snacks|egg roll kolkata
Kolkata Chicken Roll|255|13|27|11|210|Snacks|chicken kathi roll
Tandoori Momos Chicken|225|13|24|8|180|Snacks|tandoori momos
Dahi Puri|225|5|31|9|170|Snacks|dahi phuchka
Tamarind Chutney|175|1|43|0.5|25|Condiments|imli chutney
Mint Chutney|65|2|8|3|25|Condiments|hari chutney
Mayonnaise Generic|680|1|2|75|20|Condiments|mayo
Tomato Ketchup Generic|110|1|26|0|20|Condiments|ketchup
Cooking Oil Generic|884|0|0|100|10|Condiments|cooking oil,oil added
Ghee Generic|900|0|0|100|10|Condiments|clarified butter,ghee added
Butter Generic|717|0.9|0.1|81|10|Condiments|butter added
Sugar White|387|0|100|0|10|Condiments|sugar added
Honey|304|0.3|82|0|10|Condiments|honey added
Cheese Extra Generic|400|23|3|33|25|Condiments|extra cheese,cheese topping
Aloo Posto|150|3|16|8|170|East Indian|potato poppy seed curry,aloo posto
Whipped Cream Generic|260|2|9|24|30|Condiments|whipped cream topping
Apple Pie|237|1.9|34|11|125|Desserts|pie
Baby Back Ribs|280|22|5|19|200|Protein|ribs,pork ribs
Beef Carpaccio|155|22|1|7|120|Protein|carpaccio
Beef Tartare|165|20|2|9|150|Protein|tartare
Beet Salad|85|2|12|3.5|150|Salad|beetroot salad
Beignets|380|6|48|18|80|Desserts|beignet
Bibimbap|145|6.5|20|4.5|350|Asian|korean rice bowl
Bread Pudding|215|4.5|33|7.5|150|Desserts|
Breakfast Burrito|220|10|23|9.5|200|Fast Food|egg burrito
Bruschetta|185|5|25|7|100|Italian|tomato bruschetta
Caesar Salad|160|4|7|13|180|Salad|caesar
Cannoli|340|7|38|18|90|Desserts|
Caprese Salad|140|7|4|11|150|Salad|caprese,tomato mozzarella
Ceviche|95|14|5|2|180|Seafood|fish ceviche
Cheese Plate|380|22|4|31|100|Snacks|cheese platter
Chicken Quesadilla|245|15|20|12|180|Fast Food|quesadilla
Clam Chowder|95|4|10|4.5|240|Soups|chowder
Club Sandwich|235|13|22|10.5|220|Fast Food|
Crab Cakes|210|15|11|12|140|Seafood|crab cake
Creme Brulee|320|4|26|22|120|Desserts|
Croque Madame|275|14|21|15|190|Fast Food|
Cup Cakes|360|3.5|52|16|85|Desserts|cupcake
Deviled Eggs|195|11|2|16|70|Snacks|stuffed eggs
Donuts|410|5|49|22|75|Desserts|donut,doughnuts
Dumplings|185|8|26|5.5|150|Asian|potstickers,jiaozi
Edamame|122|11|10|5|120|Snacks|soy beans
Eggs Benedict|240|11|13|16|200|Breakfast|benedict
Escargots|135|16|2|7|100|French|snails
Falafel|330|13|32|18|120|Middle Eastern|falafel balls
Filet Mignon|240|26|0|15|180|Protein|beef tenderloin
Fish and Chips|225|11|23|10|300|Fast Food|fried fish and chips
Foie Gras|460|7|5|44|60|French|
French Onion Soup|65|3|8|2.5|240|Soups|onion soup
French Toast|230|7|28|10|130|Breakfast|eggy bread
Fried Calamari|240|15|18|12|150|Seafood|calamari,squid rings
Frozen Yogurt|130|3.5|24|2.5|120|Desserts|froyo
Gnocchi|165|4|32|2.5|200|Italian|potato gnocchi
Greek Salad|110|3|6|8.5|180|Salad|
Grilled Salmon|206|22|0|12.5|160|Seafood|salmon fillet
Guacamole|160|2|9|15|60|Condiments|avocado dip
Gyoza|190|8.5|24|7|150|Asian|japanese dumplings
Hamburger|250|14|24|11|200|Fast Food|beef burger,burger
Hot and Sour Soup|55|3.5|7|1.5|240|Soups|
Huevos Rancheros|165|8|16|8|220|Breakfast|mexican eggs
Hummus|170|8|14|10|60|Middle Eastern|chickpea dip
Lobster Bisque|115|5|8|7|240|Soups|
Lobster Roll Sandwich|210|14|20|8.5|180|Seafood|lobster roll
Macarons|390|7|55|16|40|Desserts|macaron
Miso Soup|35|2.5|4|1.2|200|Soups|
Mussels|120|18|5|3|200|Seafood|steamed mussels
Onion Rings|330|4|38|18|120|Fast Food|fried onion rings
Oysters|80|9|5|2.5|120|Seafood|raw oysters
Pad Thai|180|7|25|6|280|Asian|thai noodles
Paella|160|9|22|4|300|Spanish|spanish rice
Panna Cotta|220|3.5|22|13.5|120|Desserts|
Peking Duck|310|19|5|24|180|Asian|roast duck
Pho|85|6|12|1.5|380|Asian|vietnamese noodle soup,beef pho
Pork Chop|230|26|0|14|180|Protein|grilled pork chop
Poutine|260|6|27|14.5|250|Fast Food|cheese curds gravy fries
Prime Rib|290|24|0|21|200|Protein|roast beef,ribeye
Pulled Pork Sandwich|225|14|24|8|200|Fast Food|pulled pork
Ramen|110|5|16|3.5|400|Asian|japanese ramen,noodle soup
Ravioli|175|7|26|5|220|Italian|cheese ravioli
Risotto|165|4.5|24|6|220|Italian|mushroom risotto
Sashimi|125|23|0.5|3.5|120|Seafood|raw fish
Scallops|110|20|5|1|140|Seafood|seared scallops
Seaweed Salad|75|1.5|11|3|100|Salad|wakame
Shrimp and Grits|170|10|18|6.5|260|Seafood|
Spaghetti Carbonara|215|9|25|8.5|250|Italian|carbonara
Steak|250|26|0|16|200|Protein|beef steak,grilled steak
Strawberry Shortcake|260|3.5|38|11|140|Desserts|
Sushi|150|6|26|2|180|Asian|sushi roll,maki
Takoyaki|175|7|22|6.5|150|Asian|octopus balls
Tuna Tartare|140|21|2|5.5|130|Seafood|tartare
'''

LIQUID_CATEGORIES = frozenset({'Drinks', 'Mocktails'})

def serving_unit(food: dict) -> str:
    return 'ml' if food['category'] in LIQUID_CATEGORIES else 'g'

FOODS=[]
for line in ROWS.strip().splitlines():
    name,cal,protein,carbs,fat,typical,category,aliases = line.split('|')
    slug=re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-')
    FOODS.append({'id':slug,'name':name,'kcal':float(cal),'protein':float(protein),
        'carbs':float(carbs),'fat':float(fat),'default_grams':int(typical),
        'category':category,'aliases':[x.strip() for x in aliases.split(',') if x.strip()],
        'source':'illustrative_starter_not_verified'})
# Optional operator-supplied, properly licensed and source-attributed CSV.
# Columns: name,kcal,protein,carbs,fat,default_grams,category,aliases,source
def load_authorized_csv(path:str):
    if not Path(path).is_file():raise FileNotFoundError(path)
    with open(path,encoding='utf-8-sig',newline='') as stream:
        for row in csv.DictReader(stream):
            if not row.get('name','').strip() or not row.get('source','').strip():
                raise ValueError('Every imported food must have a name and provenance/source')
            slug=re.sub(r'[^a-z0-9]+','-',row['name'].lower()).strip('-')
            nums={k:float(row[k]) for k in ('kcal','protein','carbs','fat')}
            if any(not math.isfinite(v) or v<0 or v>1000 for v in nums.values()):raise ValueError('Invalid nutrition value for '+slug)
            grams=int(row.get('default_grams') or 100)
            if not (1<=grams<=5000):raise ValueError('Invalid default_grams')
            new={'id':slug,'name':row['name'].strip(),**nums,'default_grams':grams,
                 'category':row.get('category','Imported').strip(),
                 'aliases':[v.strip() for v in row.get('aliases','').split(',') if v.strip()],
                 'source':row['source'].strip()}
            # Operator-reviewed data overrides demo samples for the same named food.
            FOODS[:]=[x for x in FOODS if x['id']!=slug]
            FOODS.append(new)

if os.getenv('AUTHORIZED_FOOD_CSV'):
    load_authorized_csv(os.environ['AUTHORIZED_FOOD_CSV'])

LOOKUP={f['id']:f for f in FOODS}

def search_foods(query: str='', limit:int=40):
    from .localization import alias_match, ambiguous_search_term
    generic=ambiguous_search_term(query)
    if generic:
        return [f for f in FOODS if generic in f['name'].casefold()][:limit]
    alias=alias_match(query) if query.strip() else None
    if alias is not None:return [alias]
    q=query.strip().lower()
    if not q:return FOODS[:limit]
    terms=q.split()
    results=[f for f in FOODS if all(t in (' '.join([f['name'], f['category']]+f['aliases']).lower()) for t in terms)]
    return sorted(results,key=lambda f:(not f['name'].lower().startswith(q),len(f['name'])))[:limit]

def find_food(name:str):
    key=re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-')
    if key in LOOKUP:return LOOKUP[key]
    matches=search_foods(name,1)
    return matches[0] if matches else None

def nutrients(food:dict, grams:float):
    if not (0<grams<=5000):raise ValueError('Grams must be between 0 and 5000')
    return {k:float((Decimal(str(food[k]))*Decimal(str(grams))/Decimal('100')).quantize(Decimal('0.1'),rounding=ROUND_HALF_UP)) for k in ('kcal','protein','carbs','fat')}
