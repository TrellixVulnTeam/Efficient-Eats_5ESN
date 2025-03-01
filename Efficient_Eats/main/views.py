from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from .forms import ContactForm
from django.shortcuts import render, redirect
from .models import Restaurant, Item


# Create your views here.
def homepage(request):
    template_name = "main/home.html",
    context = {}
    return render(request=request, template_name=template_name, context=context)


def nutrition(request, restaurant_slug="", drinks=""):
    template_name = "main/nutrition.html"
    chosen_restaurant = "All"
    if restaurant_slug != "":
        if drinks == "no-drinks":
            context = {"restaurants": Restaurant.objects.all().order_by("name"),
                       "items": Item.objects.filter(restaurant__slug=restaurant_slug).exclude(type_of_item="drink").order_by("name"),
                       "drinks": False,
                       "chosen_restaurant": Restaurant.objects.filter(slug=restaurant_slug).order_by("name")[0]}
        else:
            context = {"restaurants": Restaurant.objects.all().order_by("name"),
                       "items": Item.objects.filter(restaurant__slug=restaurant_slug).order_by("name"),
                       "drinks": True,
                       "chosen_restaurant": Restaurant.objects.filter(slug=restaurant_slug).order_by("name")[0]}
    else:
        if drinks == "no-drinks":
            context = {"restaurants": Restaurant.objects.all().order_by("name"),
                       "items": Item.objects.all().exclude(type_of_item="drink").order_by("name"),
                       "drinks": False,
                       "chosen_restaurant": chosen_restaurant}
        else:
            context = {"restaurants": Restaurant.objects.all().order_by("name"),
                       "items": Item.objects.all().order_by("name"),
                       "drinks": True,
                       "chosen_restaurant": chosen_restaurant}

    return render(request=request, template_name=template_name, context=context)


def is_valid_queryparam(param):
    return param != '' and param is not None


def calculator(request, restaurant_slug=""):
    items = Item.objects.all().order_by("name")
    restaurants = Restaurant.objects.all().order_by("name")
    template_name = "main/calculator.html"

    # Search Requests
    searched_items = []
    for i in range(1, 21):
        searched_items.append(request.GET.get(f'itemName{i}'))
    searched_items_quantity = []
    for i in range(1, 21):
        searched_items_quantity.append(request.GET.get(f'itemQuantity{i}'))
    chosen_restaurant = "All"
    if restaurant_slug != "":
        items = Item.objects.filter(restaurant__slug=restaurant_slug)
        chosen_restaurant = Restaurant.objects.filter(slug=restaurant_slug)[0]
    item_list = []
    for item in items:
        item_list.append(item.name)
    options = []
    for i in range(1, 21):
        options.append(i)
    order = calculator_order(searched_items, searched_items_quantity, len(searched_items), chosen_restaurant)
    output = calculate_nutrition(order)
    context = {"restaurants": restaurants,
               "items": items,
               "chosen_restaurant": chosen_restaurant,
               "item_list": item_list,
               "options": options,
               "order": order,
               "output": output}
    return render(request, template_name, context)


def calculator_order(searched_items, searched_items_quantity, length, chosen_restaurant):
    order = []
    valid_counter = 1
    for i in range(length):
        if is_valid_queryparam(searched_items[i]):
            if chosen_restaurant != "All":
                item_name = searched_items[i]
                item_restaurant = chosen_restaurant
            else:
                itemNameComponents = searched_items[i].split(' | ')
                item_name = searched_items[i].split(' | ')[0]
                item_restaurant = "Invalid Restaurant"
                if len(itemNameComponents) > 1:
                    item_restaurant = searched_items[i].split(' | ')[1]

            itemQuery = Item.objects.filter(name__iexact=item_name).filter(restaurant__name__iexact=item_restaurant)
            if len(itemQuery) == 1:
                item = itemQuery[0]
                itemQuantity = int(searched_items_quantity[i])
                restaurant = Restaurant.objects.filter(name__iexact=item_restaurant)[0]
                attribute_inputName = "inputName" + str(valid_counter)
                attribute_itemName = "itemName" + str(valid_counter)
                attribute_itemQuantity = "itemQuantity" + str(valid_counter)
                order.append([valid_counter,  # Number of valid item in order #0
                              f"{item}",  # Name of item #1
                              int(itemQuantity),  # Quantity of item #2
                              item.id,  # ID of item #3
                              item.calories * itemQuantity,  # Calories of item in the quantity ordered #4
                              item.carbs * itemQuantity,  # Carbs of item in the quantity ordered #5
                              item.total_fat * itemQuantity,  # Fats of item in the quantity ordered #6
                              item.protein * itemQuantity,  # Protein of item in the quantity ordered #7
                              restaurant.logo,  # Logo of restaurant of the food item #8
                              attribute_inputName,  # attribute id of item #9
                              attribute_itemName,  # attribute name of item #10
                              attribute_itemQuantity,  # attribute name for select of item #11
                              restaurant.name,  # name of restaurant of item #12
                              ])
                valid_counter += 1
    return order


def calculate_nutrition(order):
    calories = 0
    total_fat = 0
    sat_fat = 0
    trans_fat = 0
    cholesterol = 0
    sodium = 0
    carbs = 0
    fiber = 0
    sugar = 0
    protein = 0
    floz = 0
    for itemList in order:
        item = Item.objects.filter(id=itemList[3])[0]
        itemQuantity = int(itemList[2])
        # Calculate all nutritional information
        calories += (itemList[4])
        total_fat += (itemList[6])
        sat_fat += (itemQuantity * item.sat_fat)
        trans_fat += (itemQuantity * item.trans_fat)
        cholesterol += (itemQuantity * item.cholesterol)
        sodium += (itemQuantity * item.sodium)
        carbs += (itemList[5])
        fiber += (itemQuantity * item.fiber)
        sugar += (itemQuantity * item.sugar)
        protein += (itemList[7])
        if item.type_of_item == "drink":
            floz = (itemQuantity * item.floz)
        else:
            floz = None

    results = {
        "calories": round(calories),
        "total_fat": round(total_fat),
        "sat_fat": round(sat_fat),
        "trans_fat": round(trans_fat),
        "cholesterol": round(cholesterol),
        "sodium": round(sodium),
        "carbs": round(carbs),
        "fiber": round(fiber),
        "sugar": round(sugar),
        "protein": round(protein),
        "floz": floz,
        "calories_from_fat": round(total_fat * 9),
        "calories_from_protein": round(protein * 4),
        "calories_from_carbs": round(carbs * 4),
        "total_fat_daily_value": round((total_fat / 65) * 100),
        "sat_fat_daily_value": round((sat_fat / 20) * 100),
        "cholesterol_daily_value": round((cholesterol / 300) * 100),
        "sodium_daily_value": round((sodium / 2400) * 100),
        "carbs_daily_value": round((carbs / 300) * 100),
        "fiber_daily_value": round((fiber / 25) * 100),
        "carbs_efficiency": round((((carbs * 4) / calories) * 100), 1) if calories > 0 else None,
        "fat_efficiency": round((((total_fat * 9) / calories) * 100), 1) if calories > 0 else None,
        "protein_efficiency": round((((protein * 4) / calories) * 100), 1) if calories > 0 else None,
    }
    return results


def lookup(request, restaurant_slug="", item_slug=""):
    template_name = "main/lookup.html"
    chosen_restaurant = "All"
    restaurants = Restaurant.objects.all().order_by("name")
    items = Item.objects.all().order_by("name")
    myItem = [request.GET.get('myInput')]
    if restaurant_slug != "":
        chosen_restaurant = Restaurant.objects.filter(slug__iexact=restaurant_slug)[0]
        items = Item.objects.filter(restaurant__slug__iexact=restaurant_slug)
        if item_slug != "" and myItem[0] is None:
            myItem = Item.objects.filter(restaurant__slug__iexact=restaurant_slug).filter(slug__iexact=item_slug)
    order = calculator_order(myItem, [1], len(myItem), chosen_restaurant)
    output = calculate_nutrition(order)
    context = {
        "items": items,
        "restaurants": restaurants,
        "chosen_restaurant": chosen_restaurant,
        "order": order,
        "output": output,
    }

    return render(request, template_name, context)


def methodology(request):
    template_name = "main/methodology.html"

    return render(request, template_name)


def contact(request, success=""):
    submitted = False
    template_name = "main/contact.html"
    if request.method == 'GET':
        form = ContactForm()
    else:
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            from_email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            try:
                send_mail(subject, message, from_email, ['markbekker1998@gmail.com'])
            except BadHeaderError:
                return HttpResponse('Invalid form submission.')
            return redirect("success/")
    if success != "":
        submitted = True

    context = {"form": form,
               "submitted": submitted}
    return render(request, template_name, context)
