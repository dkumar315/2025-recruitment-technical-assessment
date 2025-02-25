from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Recipe(CookbookEntry):
	required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
	cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook = {}

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> Union[str | None]:
	if not recipeName or not isinstance(recipeName, str):
		return None
	
	parsed_name = re.sub(r'[-_]+', ' ', recipeName)
	parsed_name = re.sub(r'[^a-zA-Z ]', '', parsed_name)
	parsed_name = ' '.join(parsed_name.split()).title()
	
	return parsed_name if parsed_name else None


# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
	data = request.get_json()

	if "type" not in data or "name" not in data:
		return "Missing required fields", 400

	entry_type = data["type"]
	name = data["name"]

	if entry_type not in ["recipe", "ingredient"]:
		return "Invalid type", 400

	if name in cookbook:
		return "Entry name must be unique", 400

	if entry_type == "recipe":
		if "requiredItems" not in data or not isinstance(data["requiredItems"], list):
			return "Invalid requiredItems field", 400

		unique_items = {}
		for item in data["requiredItems"]:
			if "name" not in item or "quantity" not in item or not isinstance(item["quantity"], int):
				return "Invalid requiredItem format", 400
			if item["name"] in unique_items:
				return "Duplicate requiredItem detected", 400

			unique_items[item["name"]] = item["quantity"]

		cookbook[name] = {"type": "recipe", "requiredItems": unique_items}

	elif entry_type == "ingredient":
		if "cookTime" not in data or not isinstance(data["cookTime"], int) or data["cookTime"] < 0:
			return "Invalid cookTime", 400

		cookbook[name] = {"type": "ingredient", "cookTime": data["cookTime"]}
		
	return "", 200


# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():
	recipe_name = request.args.get("name")
	if not recipe_name or recipe_name not in cookbook:
		return "Recipe not found", 400

	entry = cookbook[recipe_name]
	if not entry or entry["type"] != "recipe":
		return "Entry is not a recipe", 400

	def get_summary(name, quantity = 1):
		if name not in cookbook:
			return None, None

		entry = cookbook[name]
		if entry["type"] == "ingredient":
			return entry["cookTime"] * quantity, {name: quantity}

		total_cook_time = 0
		ingredient_counts = {}

		for item_name, item_quantity in entry["requiredItems"].items():
			item_cook_time, item_ingredients = get_summary(item_name, item_quantity * quantity)
			if item_cook_time is None:
				return None, None

			total_cook_time += item_cook_time

			for ing_name, ing_qty in item_ingredients.items():
				if ing_name in ingredient_counts:
					ingredient_counts[ing_name] += ing_qty
				else:
					ingredient_counts[ing_name] = ing_qty

		return total_cook_time, ingredient_counts

	total_cook_time, ingredient_counts = get_summary(recipe_name)
	if total_cook_time is None:
		return "Invalid recipe structure", 400

	return jsonify({
		"name": recipe_name,
		"cookTime": total_cook_time,
		"ingredients": ingredient_counts
	}), 200


# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)
