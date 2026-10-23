# Usability improvements (Problem 9)

## Front end

1. **Garment-type filter on Products**  
   Shoppers can narrow the catalogue by `garment_type` without opening chat. Helps parents/students who already know they want a hoodie vs a tee.

2. **Recently viewed link in the nav**  
   After opening a detail page, “Recently viewed” jumps back to the last item. Reduces re-hunting through a long grid during comparison shopping.

## Agent / backend

1. **Search result cap (8) + structured `ProductCard`s**  
   Catalogue search returns a bounded card payload so the page stays scannable and chat does not list every SKU at once.

2. **Suggestion chips after search**  
   The chat response includes short follow-up prompts (“Want stock for a size?”). Speeds the next useful question without another blank compose.
