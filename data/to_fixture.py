import json

with open('ingredients.json', encoding='utf-8') as f:
    raw_data = json.load(f)

fixture = []
for i, item in enumerate(raw_data, start=1):
    fixture.append({
        "model": "recipes.ingredient",
        "pk": i,
        "fields": item
    })

with open('ingredients_fixture.json', 'w', encoding='utf-8') as f:
    json.dump(fixture, f, ensure_ascii=False, indent=2)
