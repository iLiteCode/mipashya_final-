
from decimal import Decimal
from multiprocessing import context
from sqlite3 import IntegrityError
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed , HttpResponseRedirect
import pytz
from .models import Hotels,Rooms,Reservation
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.all()  # This works with your custom model
from django.contrib.auth.decorators import login_required
import datetime
# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from .models import Rooms, Hotels
from .forms import RoomForm

from datetime import datetime, timezone
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import user_passes_test
from user.models import HotelStaff



def homepage(request):
    all_location = Hotels.objects.values_list('location','id').distinct().order_by()
    if request.method =="POST":
        try:
            print(request.POST)
            hotel = Hotels.objects.all().get(id=int(request.POST['search_location']))
            rr = []
            
            #for finding the reserved rooms on this time period for excluding from the query set
            for each_reservation in Reservation.objects.all():
                if str(each_reservation.check_in) < str(request.POST['cin']) and str(each_reservation.check_out) < str(request.POST['cout']):
                    pass
                elif str(each_reservation.check_in) > str(request.POST['cin']) and str(each_reservation.check_out) > str(request.POST['cout']):
                    pass
                else:
                    rr.append(each_reservation.room.id)
                
            room = Rooms.objects.all().filter(hotel=hotel,capacity__gte = int(request.POST['capacity'])).exclude(id__in=rr)
            if len(room) == 0:
                messages.warning(request,"Sorry No Rooms Are Available on this time period")
            data = {'rooms':room,'all_location':all_location,'flag':True}
            response = render(request,'rooms/index.html',data)
        except Exception as e:
            messages.error(request,e)
            response = render(request,'rooms/index.html',{'all_location':all_location})


    else:
        
        
        data = {'all_location':all_location}
        response = render(request,'rooms/index.html',data)
    return HttpResponse(response)


from django.db.models import Q
from user.models import HotelStaff
from .models import Hotels
from .forms import HotelAssignmentForm
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

def check_hotel_management_authority(user):
    """Check if user has authority to manage hotels"""
    if not user.is_authenticated:
        return False
    return user.is_superuser or getattr(user, 'is_authority_to_manage_hotel', False)

def assign_hotel_to_staff(request):
    # If user doesn't have permission, they'll be redirected to home with message
    if not check_hotel_management_authority(request.user):
            messages.error(request, "You are not an permissions to maange this hotel or you not verified as maintainers ")
            return redirect('maintainer_panel')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'assign':
            staff_id = request.POST.get('staff_id')  # HSTF697 format
            hotel_id = request.POST.get('hotel_id')  # Numeric ID
            
            try:
                staff = HotelStaff.objects.get(staff_id=staff_id)
                hotel = Hotels.objects.get(id=hotel_id)
                
                # Handle existing assignment
                if staff.hotel:
                    messages.info(request, f"Staff was previously assigned to {staff.hotel.name}")
                
                staff.hotel = hotel
                staff.save()
                messages.success(request, f"Assigned {staff.user.get_full_name()} to {hotel.name}")
                
            except HotelStaff.DoesNotExist:
                messages.error(request, f"Staff member {staff_id} not found")
            except Hotels.DoesNotExist:
                messages.error(request, f"Hotel {hotel_id} not found")
            
            return redirect('assign-hotel')
        
        elif action == 'unassign':
            staff_id = request.POST.get('staff_id')
            try:
                staff = HotelStaff.objects.get(staff_id=staff_id)
                if staff.hotel:
                    hotel_name = staff.hotel.name
                    staff.hotel = None
                    staff.save()
                    messages.success(request, f"Unassigned from {hotel_name}")
                else:
                    messages.warning(request, "No assignment found")
            except HotelStaff.DoesNotExist:
                messages.error(request, f"Staff member {staff_id} not found")
            
            return redirect('assign-hotel')

    # GET request handling
    context = {
        'assigned_staff': HotelStaff.objects.filter(hotel__isnull=False)
                         .select_related('user', 'hotel'),
        'unassigned_staff': HotelStaff.objects.filter(hotel__isnull=True)
                           .select_related('user'),
        'hotels': Hotels.objects.all(),
    }
    return render(request, 'admin/assign_hotel.html', context)

@user_passes_test(lambda u: u.is_authority_to_manage_hotel, login_url='home')
def manage_hotel_assignments(request):
    assignments = HotelStaff.objects.filter(hotel__isnull=False) \
                     .select_related('user', 'hotel') \
                     .order_by('hotel__name')
    
    unassigned_hotels = Hotels.objects.exclude(
        id__in=assignments.values('hotel_id')
    )
    
    return render(request, 'admin/manage_assignments.html', {
        'assignments': assignments,
        'unassigned_hotels': unassigned_hotels,
    })
@user_passes_test(lambda u: u.is_authority_to_manage_hotel, login_url='home')
def edit_hotel_assignment(request, pk):  # Changed from assignment_id to pk
    assignment = get_object_or_404(HotelStaff, pk=pk)
    
    if request.method == 'POST':
        form = HotelAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, "Assignment updated successfully")
            return redirect('manage-hotel')
    else:
        form = HotelAssignmentForm(instance=assignment)
    
    return render(request, 'admin/edit_assignment.html', {
        'form': form,
        'assignment': assignment,
    })

@user_passes_test(lambda u: u.is_authority_to_manage_hotel, login_url='home')
def unassign_staff(request, pk):  # Changed from assignment_id to pk
    if request.method == 'POST':
        assignment = get_object_or_404(HotelStaff, pk=pk)
        if assignment.hotel:
            messages.success(request, 
                f"Unassigned {assignment.user.get_full_name()} from {assignment.hotel.name}"
            )
            assignment.hotel = None
            assignment.save()
        else:
            messages.warning(request, "No assignment found")
    
    return redirect('manage-hotel')

@user_passes_test(lambda u: u.is_authority_to_manage_hotel, login_url='home')
def unassign_staff(request, pk):
    if request.method == 'POST':
        assignment = get_object_or_404(HotelStaff, pk=pk)
        if assignment.hotel:
            messages.success(request, 
                f"Unassigned {assignment.user.get_full_name()} from {assignment.hotel.name}"
            )
            assignment.hotel = None
            assignment.save()
        else:
            messages.warning(request, "No assignment found")
    
    return redirect('manage-hotel')

@user_passes_test(lambda u: u.is_authority_to_manage_hotel, login_url='home')
def staff_list(request):
    staff_members = HotelStaff.objects.select_related('user', 'hotel').all()
    return render(request, 'admin/staff_list.html', {
        'staff_members': staff_members
    })

@login_required(login_url='/')
def hotel_staff_edit_room(request, room_id):
    if not request.user.is_staff:
        return HttpResponse('Access Denied')  # Staff-only access

    try:
        room = get_object_or_404(Rooms, id=room_id)
        
        if request.method == 'POST':
            form = RoomForm(request.POST, request.FILES, instance=room)
            
            if form.is_valid():
                form.save()  # Save the updated room to the database
                messages.success(request, "Room details updated successfully.")
                return redirect('staffpanel')
            else:
                messages.error(request, "Form validation failed. Please correct the errors below.")
                hotels = Hotels.objects.all()  # Get hotels for select options
                return render(request, 'hotel_staff/edit_room.html', {
                    'form': form,
                    'room': room,
                    'hotels': hotels
                })

        else:  # GET request
            form = RoomForm(instance=room)  # Pre-populate form with existing data
            hotels = Hotels.objects.all()  # Get all hotels for select options
            return render(request, 'hotel_staff/edit_room.html', {
                'form': form,
                'hotels': hotels,
                'room': room
            })

    except Exception as e:
        messages.error(request, f"Error processing request: {e}")
        return redirect('staffpanel')
    
# for edti rooms
@login_required(login_url='/')
def hotel_staff_edit_location(request):
    if not hasattr(request.user, 'hotel_staff_profile'):
        return HttpResponse('Access Denied - Not a Hotel Staff')

    if request.method == "POST":
        try:
            hotel = hotel(
                name=request.POST['name'],
                location=request.POST['location'],
                state=request.POST['state'],
                country=request.POST['country'],
                gst_no=request.POST['gst_no'],
                main_image=request.FILES.get('main_image')
            )
            hotel.full_clean()
            hotel.save()
            staff = HotelStaff.objects.get(user=request.user)
            staff.hotel = hotel
            staff.save()
            messages.success(request, "New hotel location added successfully.")
            return redirect('staffpanel')
        except Exception as e:
            messages.error(request, f"Error adding location: {e}")

    return render(request, 'staffpanel')

@login_required(login_url='/')
def add_new_location(request):
    if not request.user.is_staff or not hasattr(request.user, 'hotel_staff_profile'):
        return HttpResponseForbidden("Not Allowed - Only hotel staff can add locations")

    if request.method == "POST":
        try:
            name = request.POST.get('hotel_name', '').strip()
            owner = request.POST.get('new_owner', '').strip()
            location = request.POST.get('new_city', '').strip()
            state = request.POST.get('new_state', '').strip()
            country = request.POST.get('new_country', '').strip()

            if not all([name, owner, location, state, country]):
                messages.error(request, "All fields are required")
                return redirect("staffpanel")

            if Hotels.objects.filter(location=location, state=state).exists():
                messages.warning(request, "A hotel in this location already exists")
                return redirect("staffpanel")

            new_hotel = Hotels.objects.create(
                name=name,
                owner=owner,
                location=location,
                state=state,
                country=country,
                created_by=request.user.hotel_staff_profile
            )
            new_hotel.assigned_staff.add(request.user.hotel_staff_profile)
            messages.success(request, f"{name} in {location} added successfully!")
            messages.warning(request, f"hello {name} please you have wait for this  {location} assigned you from adminisgtrations !")
            return redirect("staffpanel")

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect("staffpanel")

    return render(request, 'staffpanel.html')  # Adjust template name if needed
#contact page
def contactpage(request):

    messages.warning(request, f"Hello, user you don't have permissions to chage this essential data pls contact to administator.")
    return HttpResponse(render(request,'admin/contact-admin.html'))


@login_required(login_url='/')
def hotel_view_hotels(request):
    if not request.user.is_staff or not hasattr(request.user, 'hotel_staff_profile'):
        return HttpResponseForbidden("Contact administrator")
    
    staff = request.user.hotel_staff_profile
    hotels = Hotels.objects.filter(created_by=staff)
    return render(request, 'hotel_staff/hotels.html', {'hotels': hotels})


# @login_required(login_url='/')
# def hotel_view_hotels(request):
#     if not request.user.is_staff or not hasattr(request.user, 'hotel_staff_profile'):
#         return HttpResponseForbidden("contact")

#     staff = request.user.hotel_staff_profile
#     hotels = staff.assigned_hotels.all()
#     return render(request, 'hotel_staff/hotels.html', {'hotels': hotels})

@login_required(login_url='/')
def hotel_staff_add_room(request):
    """
    Allows hotel staff to add rooms to their assigned hotels
    - Only shows hotels the staff is assigned to
    - Handles file uploads and room creation
    - Validates all inputs
    """
    if not hasattr(request.user, 'hotel_staff_profile'):
        return HttpResponseForbidden('Access Denied - Hotel Staff Only')

    staff = request.user.hotel_staff_profile
    assigned_hotels = staff.assigned_hotels.all()

    if request.method == "POST":
        try:
            hotel_id = int(request.POST.get('hotel'))
            hotel = assigned_hotels.get(id=hotel_id)  # Ensures staff has access
            
            # Create room with basic info
            new_room = Rooms(
                hotel=hotel,
                room_number=request.POST.get('room_number', '').strip(),
                room_type=request.POST.get('roomtype'),
                capacity=int(request.POST.get('capacity', 1)),
                size=int(request.POST.get('size', 0)),
                price=Decimal(request.POST.get('price', 0.0)),
                discount=Decimal(request.POST.get('discount', 0.0)),
                status=request.POST.get('status', '1'),  # Default to available
                description=request.POST.get('description', '').strip(),
                heading=request.POST.get('heading', '').strip(),
                food_facility=request.POST.get('food_facility') == 'on',
                parking=request.POST.get('parking') == 'on',
            )

            # Handle time fields
            if check_in := request.POST.get('check_in_time'):
                new_room.check_in_time = check_in
            if check_out := request.POST.get('check_out_time'):
                new_room.check_out_time = check_out

            # Handle image uploads (up to 15 images)
            for i in range(1, 16):
                if f'image{i}' in request.FILES:
                    setattr(new_room, f'image{i}', request.FILES[f'image{i}'])

            new_room.full_clean()
            new_room.save()
            messages.success(request, f"Room {new_room.room_number} added successfully!")
            
        except Hotels.DoesNotExist:
            messages.error(request, "Invalid hotel selection")
        except ValueError as e:
            messages.error(request, f"Invalid input: {str(e)}")
        except Exception as e:
            messages.error(request, f"Error adding room: {str(e)}")
        
        return redirect('staffpanel')

    # GET request - show form
    context = {
        'hotels': assigned_hotels.values_list('name', 'id'),
        'room_types': Rooms.ROOM_TYPE,
        'room_statuses': Rooms.ROOM_STATUS
    }
    return render(request, 'hotel_staff/add_room.html', context)


@login_required(login_url='/')
def view_room(request, room_id):
    if not hasattr(request.user, 'hotel_staff_profile'):
        return HttpResponseForbidden('Access Denied - Hotel Staff Only')
    try:
        room = Rooms.objects.get(id=room_id)
    except Rooms.DoesNotExist:
        raise Http404("Room not found")
    reservations = Reservation.objects.filter(room=room)
    current_date = datetime.now().date()
    for reservation in reservations:
        if reservation.check_out < current_date:
            reservation.status = 'past'
        elif reservation.check_in <= current_date and reservation.check_out >= current_date:
            reservation.status = 'current'
        else:
            reservation.status = 'future'
    return render(request, 'hotel_staff/viewroom.html', {
        'room': room,
        'reservations': reservations,
        'current_date': current_date
    })


@login_required(login_url='/')
def hotel_staff_panel(request):
    """
    Displays the hotel staff panel with a list of rooms and stats for assigned hotels.
    """
    if hasattr(request.user, 'maintainer_profile'):
        messages.warning(request,"you don't have permissions to staff pannel ")
        return redirect('maintainer_panel')
    
    if not hasattr(request.user, 'hotel_staff_profile'):
        return render(request, 'hotel_staff/panel.html', {
            'error_title': 'Access Denied',
            'error_message': 'This page is only accessible to hotel staff members.'
        }, status=403)
    
    try:
        # Optimized query to get staff with hotel in one query
        staff = HotelStaff.objects.select_related('hotel').get(user=request.user)
        
        # If no hotel is associated with the staff member, show a warning and redirect to add hotel page
        if not staff.hotel:
            messages.warning(request, 'Hello, you need to add your hotel and rooms to increase your business.')
            return redirect('add_hotel')  # Assuming 'add_hotel' is the URL name to allow the user to add a hotel
            
        hotel = staff.hotel
        # Get all rooms for this hotel
        rooms = Rooms.objects.filter(hotel=hotel)
        total_rooms = rooms.count()
        
        # Calculate counts with zero division protection
        available_rooms = rooms.filter(status='1').count() if total_rooms else 0
        unavailable_rooms = rooms.filter(status='2').count() if total_rooms else 0
        reservations = Reservation.objects.filter(room__hotel=hotel).count()
        
        # Calculate percentages with zero division protection
        total_rooms_nonzero = total_rooms or 1  # Prevent division by zero in template
        available_percent = (available_rooms / total_rooms_nonzero * 100) 
        unavailable_percent = (unavailable_rooms / total_rooms_nonzero * 100)
        reservations_percent = (reservations / total_rooms_nonzero * 100)
        
        context = {
            'hotel': hotel,
            'rooms': rooms,
            'total_rooms': total_rooms,
            'available_rooms': available_rooms,
            'available_percent': available_percent,
            'unavailable_rooms': unavailable_rooms,
            'unavailable_percent': unavailable_percent,
            'reservations': reservations,
            'reservations_percent': reservations_percent,
            # Additional stats similar to maintainer panel
            'hotel_locations': Hotels.objects.values_list('location', flat=True).distinct().order_by('location'),
        }
        
        return render(request, 'hotel_staff/panel.html', context)
        
    except HotelStaff.DoesNotExist:
        return render(request, 'hotel_staff/panel.html', {
            'error_title': 'Profile Not Found',
            'error_message': 'Your staff profile could not be found. Please contact administration.'
        }, status=404)
    except Exception as e:
        # Catch any unexpected errors and display them
        return render(request, 'hotel_staff/panel.html', {
            'error_title': 'An error occurred',
            'error_message': f'An unexpected error occurred: {str(e)}'
        }, status=500)





@login_required(login_url='/')
def list_rooms(request):
    """
    Displays a list of rooms for hotels assigned to the logged-in staff.
    """
    if not hasattr(request.user, 'hotel_staff_profile'):
        return HttpResponseForbidden('Access Denied - Hotel Staff Only')

    staff = request.user.hotel_staff_profile
    assigned_hotels = staff.assigned_hotels.all()
    
    # Fetch all rooms from the staff's assigned hotels
    rooms = Rooms.objects.filter(hotel__in=assigned_hotels)

    # Add calculated fields for discounted price and saved money
    for room in rooms:
        room.discounted_price = room.price * (1 - room.discount / 100)
        room.saved_money = room.price - room.discounted_price

    context = {
        'rooms': rooms,
    }
    return render(request, 'hotel_staff/list_rooms.html', context)


def get_hotels_for_user(user):
    if hasattr(user, 'maintainer_profile'):
        # Maintainers see all hotels
        return Hotels.objects.all().values_list('name', 'id')
    elif hasattr(user, 'hotel_staff_profile'):
        # Staff only see hotels they're assigned to
        return user.hotel_staff_profile.assigned_hotels.all().values_list('name', 'id')
    else:
        # Regular users see all (or none)
        return Hotels.objects.none()

#for showing all bookings to staff

@login_required(login_url='/')
def hotel_staff_bookings(request):

    
    if not hasattr(request.user, 'hotel_staff_profile'):
        messages.warning(request,"you don't have permissions to maintainer pannel ")
        return redirect('/')
    

    
    

    staff = HotelStaff.objects.get(user=request.user)
    bookings = Reservation.objects.filter(room__hotel=staff.hotel)
    current_date = datetime.now().date()

    for booking in bookings:
        if booking.check_out < current_date:
            booking.status = 'past'
        elif booking.check_in <= current_date <= booking.check_out:
            booking.status = 'current'
        else:
            booking.status = 'future'


    if not bookings:
        messages.warning(request, "Hey staff No booking found ")

    if  bookings:
        messages.success(request, "Hey staff booking found ")

    return render(request, 'hotel_staff/bookings.html', {
        'bookings': bookings,
        'current_date': current_date,
    })





# Maintainer Views
@user_passes_test(lambda u: u.is_maintainer, login_url='/')
@login_required(login_url='/')
def maintainer_panel(request):
    if not hasattr(request.user, 'maintainer_profile'):
        messages.warning(request,"you don't have permissions ")
        return redirect('/')

    # Optimized database queries
    rooms = Rooms.objects.all()
    total_rooms = rooms.count()
    
    # Handle case where total_rooms is 0 to prevent division by zero
    if total_rooms == 0:
        available_rooms = 0
        unavailable_rooms = 0
    else:
        available_rooms = rooms.filter(status='1').count()
        unavailable_rooms = rooms.filter(status='2').count()
    
    total_hotels = Hotels.objects.count()
    reserved = Reservation.objects.count()
    hotel_locations = Hotels.objects.values_list('location', 'id').distinct().order_by('location')

    context = {
        'location': hotel_locations,
        'reserved': reserved,
        'rooms': rooms,
        'total_rooms': total_rooms or 1,  # Ensure at least 1 to prevent template division by zero
        'available': available_rooms,
        'unavailable': unavailable_rooms,
        'total_hotels': total_hotels,
    }
    return render(request, 'maintainer/panel.html', context)

@user_passes_test(lambda u: u.is_maintainer, login_url='/')
@login_required(login_url='/')
def maintainer_all_bookings(request):
    if not hasattr(request.user, 'maintainer_profile'):
        messages.warning(request,"you don't have permissions ")
        return redirect('/')

    bookings = Reservation.objects.all()
    current_date = datetime.now().date()

    if not bookings:
        messages.warning(request, "No Bookings Found")

    for booking in bookings:
        if booking.check_out < current_date:
            booking.status = 'past'
        elif booking.check_in <= current_date <= booking.check_out:
            booking.status = 'current'
        else:
            booking.status = 'future'

    return render(request, 'maintainer/bookings.html', {
        'bookings': bookings,
        'current_date': current_date,
    })

@user_passes_test(lambda u: u.is_maintainer, login_url='/')
@login_required(login_url='/')
def maintainer_view_rooms(request):
    if not hasattr(request.user, 'maintainer_profile'):
        messages.warning(request,"you don't have permissions ")
        return redirect('/')

    rooms = Rooms.objects.all()
    return render(request, 'maintainer/rooms.html', {'rooms': rooms})

@user_passes_test(lambda u: u.is_maintainer, login_url='/')
@login_required(login_url='/')
def maintainer_view_hotels(request):
    if not hasattr(request.user, 'maintainer_profile'):
        messages.warning(request,"you don't have permissions ")
        return redirect('/')

    hotels = Hotels.objects.all()
    return render(request, 'maintainer/hotels.html', {'hotels': hotels})

@user_passes_test(lambda u: u.is_maintainer, login_url='/')
@login_required(login_url='/')
def maintainer_edit_hotel(request, hotel_id):
    if not hasattr(request.user, 'maintainer_profile'):
        messages.warning(request,"you don't have permissions ")
        return redirect('/')

    hotels = get_object_or_404(Hotels, id=hotel_id)
    if request.method == "POST":
        try:
            hotels.name = request.POST['hotel_name'] 
            hotels.owner = request.POST['new_owner']
            hotels.location = request.POST['new_city']
            hotels.state = request.POST['new_state']
            hotels.country = request.POST['new_country']
            if 'main_image' in request.FILES:
                hotels.main_image = request.FILES['main_image']
            hotels.full_clean()
            hotels.save()
            messages.success(request, "Hotel updated successfully.")
            return redirect('maintainer_view_hotels')
        except Exception as e:
            messages.error(request, f"Error updating hotel: {e}")
    
    return render(request, 'maintainer/edit_hotels.html', {'hotel': hotels})

@user_passes_test(lambda u: u.is_maintainer, login_url='/')
@login_required(login_url='/')
def maintainer_edit_room(request):
    if not hasattr(request.user, 'maintainer_profile'):
        messages.warning(request,"you don't have permissions ")
        return redirect('/')

    if request.method == 'POST':
        room_id = request.POST.get('roomid')
        
        if not room_id:
            messages.error(request, "Room ID is missing.")
            return redirect('maintainer_panel')

        try:
            room = get_object_or_404(Rooms, id=room_id)
            form = RoomForm(request.POST, request.FILES, instance=room)  # Assumes RoomForm exists

            if form.is_valid():
                form.save()
                messages.success(request, "Room details updated successfully.")
                return redirect('maintainer_panel')
            else:
                messages.error(request, "Form validation failed. Please correct the errors below.")
                return render(request, 'maintainer/edit_room.html', {'form': form, 'room': room})

        except Rooms.DoesNotExist:
            messages.error(request, "Room not found.")
            return redirect('maintainer_panel')
        except Exception as e:
            messages.error(request, f"Error updating room: {e}")
            return render(request, 'maintainer/edit_room.html', {'form': form, 'room': room})

    else:
        room_id = request.GET.get('roomid')
        if not room_id:
            messages.error(request, "Room ID is missing.")
            return redirect('maintainer_panel')

        try:
            room = get_object_or_404(Rooms, id=room_id)
            form = RoomForm(instance=room)
            hotels = Hotels.objects.all()
            return render(request, 'maintainer/edit_room.html', {'form': form, 'hotels': hotels, 'room': room})
        except Rooms.DoesNotExist:
            messages.error(request, "Room not found.")
            return redirect('maintainer_panel')

@user_passes_test(lambda u: u.is_maintainer, login_url='/')
@login_required(login_url='/')
def maintainer_add_new_room(request):
    if not hasattr(request.user, 'maintainer_profile'):
        messages.warning(request,"you don't have permissions ")
        return redirect('/')

    if request.method == "POST" and request.FILES:
        try:
            hotel = Hotels.objects.get(id=int(request.POST['hotel']))
            check_in_time = request.POST.get('check_in_time')
            check_out_time = request.POST.get('check_out_time')

            new_room = Rooms(
                room_number=request.POST.get('room_number'),
                room_type=request.POST.get('roomtype'),
                capacity=int(request.POST.get('capacity', 0)),
                size=int(request.POST.get('size', 0)),
                price=float(request.POST.get('price', 0.0)),
                discount=float(request.POST.get('discount', 0.0)),
                status=request.POST.get('status'),
                hotel=hotel,
                description=request.POST.get('description'),
                heading=request.POST.get('heading'),
                food_facility=bool(request.POST.get('food_facility', False)),
                parking=bool(request.POST.get('parking', False)),
                check_in_time=check_in_time if check_in_time else None,
                check_out_time=check_out_time if check_out_time else None,
            )

            if 'image1' in request.FILES:
                new_room.image1 = request.FILES['image1']
            if 'image2' in request.FILES:
                new_room.image2 = request.FILES['image2']
            if 'image3' in request.FILES:
                new_room.image3 = request.FILES['image3']

            new_room.full_clean()
            new_room.save()
            messages.success(request, "New Room Added Successfully")
        except Exception as e:
            messages.error(request, f"Error adding room: {e}")
        return redirect('maintainer_panel')

    hotels = Hotels.objects.all()
    return render(request, 'maintainer/add_room.html', {'hotels': hotels})

@user_passes_test(lambda u: u.is_maintainer, login_url='/')
@login_required(login_url='/')
def maintainer_view_room(request):
    if not hasattr(request.user, 'maintainer_profile'):
        messages.warning(request,"you don't have permissions ")
        return redirect('/')

    room_id = request.GET.get('roomid')
    if not room_id:
        messages.error(request, "Room ID is required.")
        return HttpResponse(render(request, 'maintainer/view_room.html', {'error': 'Room ID is required.'}))

    try:
        room = Rooms.objects.get(id=room_id)
    except Rooms.DoesNotExist:
        raise Http404("Room not found")

    reservations = Reservation.objects.filter(room=room)
    current_date = datetime.now().date()

    for reservation in reservations:
        if reservation.check_out < current_date:
            reservation.status = 'past'
        elif reservation.check_in <= current_date and reservation.check_out >= current_date:
            reservation.status = 'current'
        else:
            reservation.status = 'future'

    return HttpResponse(render(request, 'maintainer/view_room.html', {
        'room': room,
        'reservations': reservations,
        'current_date': current_date
    }))

@user_passes_test(lambda u: u.is_maintainer, login_url='/')
@login_required(login_url='/')
def maintainer_add_new_location(request):
    # Ensure user is a maintainer
    if not getattr(request.user, 'maintainer_profile', None):
        return HttpResponseForbidden('Access Denied - Not a Maintainer')

    if request.method == "POST":
        # Safely get data from POST request
        name = request.POST.get('hotel_name', '').strip()
        owner = request.POST.get('new_owner', '').strip()
        location = request.POST.get('new_city', '').strip()
        state = request.POST.get('new_state', '').strip()
        country = request.POST.get('new_country', '').strip()

        # Validate required fields
        if not all([name, owner, location, state, country]):
            messages.error(request, "All fields are required!")
            return redirect("maintainer_panel")

        # Create and save new hotel
        try:
            Hotels.objects.create(
                name=name,
                owner=owner,
                location=location,
                state=state,
                country=country
            )
            messages.success(request, f"{name} in {location} added successfully!")
        except IntegrityError:
            messages.error(request, "Hotel with similar details already exists")
        except Exception as e:
            messages.error(request, f"Error creating hotel: {str(e)}")

        return redirect("maintainer_panel")

    # GET request - show form with all hotels
    context = {
        'all_hotels': Hotels.objects.all().values_list('name', 'id'),
        'location': Hotels.objects.all().values_list('name', 'id')  # For backward compatibility
    }
    return render(request, 'maintainer/add_location.html', context)



# userall
@login_required(login_url='/')
def user_bookings(request):
    if request.user.is_authenticated == False:
        return redirect('userloginpage')
    
    user = User.objects.get(id=request.user.id)
    bookings = Reservation.objects.filter(guest=user)

    # Get the current date
    current_date = datetime.now().date()

    if not bookings:
        messages.warning(request, "No Bookings Found")

    return render(request, 'user/mybookings.html', {'bookings': bookings, 'current_date': current_date})



#For booking the room
@login_required(login_url='/')
def book_room(request):
    
    if request.method == "POST":

        room_id = request.POST['room_id']
        
        room = Rooms.objects.all().get(id=room_id)
        #for finding the reserved rooms on this time period for excluding from the query set
        for each_reservation in Reservation.objects.all().filter(room=room):
            if str(each_reservation.check_in) < str(request.POST['check_in']) and str(each_reservation.check_out) < str(request.POST['check_out']):
                pass
            elif str(each_reservation.check_in) > str(request.POST['check_in']) and str(each_reservation.check_out) > str(request.POST['check_out']):
                pass
            else:
                messages.warning(request,"Sorry This Room is unavailable for Booking")
                return redirect("homepage")
            
        current_user = request.user
        total_person = int(request.POST['person'])
        booking_id = str(room_id) + str(datetime.now())  # using datetime.now() after import

        reservation = Reservation()
        room_object = Rooms.objects.all().get(id=room_id)
        room_object.status = '2'
        
        user_object = User.objects.all().get(username=current_user)

        reservation.guest = user_object
        reservation.room = room_object
        person = total_person
        reservation.check_in = request.POST['check_in']
        reservation.check_out = request.POST['check_out']

        reservation.save()

        messages.success(request,"Congratulations! Booking Successfull")

        return redirect("homepage")
    else:
        return HttpResponse('Access Denied')



#about
def aboutpage(request):
    return HttpResponse(render(request,'about.html'))












def Check_list(request):
    # Get all hotels for the location filter
    hotels = Hotels.objects.all()

    # Filter rooms based on query parameters
    rooms = Rooms.objects.filter(status='1')  # Only 'available' rooms
    location = request.GET.get('location')
    if location:
        rooms = rooms.filter(hotel__location=location)

    # Check for amenities (filters)
    if 'ac' in request.GET:
        rooms = rooms.filter(ac=True)
    if 'fan' in request.GET:
        rooms = rooms.filter(fan=True)
    if 'wifi' in request.GET:
        rooms = rooms.filter(wifi=True)
    if 'parking' in request.GET:
        rooms = rooms.filter(parking=True)
    if 'heater' in request.GET:
        rooms = rooms.filter(heater=True)
    if 'food_facility' in request.GET:
        rooms = rooms.filter(food_facility=True)

    # Filter based on other POST values
    if request.method == 'POST':
        location = request.POST.get('search_location')
        if location:
            rooms = rooms.filter(hotel__location=location)

        check_in = request.POST.get('cin')
        check_out = request.POST.get('cout')
        capacity = request.POST.get('capacity')

        if check_in and check_out:
            # Logic to exclude booked rooms in the selected date range
            booked_rooms = []
            for reservation in Reservation.objects.all():
                if (str(reservation.check_in) < str(check_in) and str(reservation.check_out) < str(check_out)) or \
                   (str(reservation.check_in) > str(check_in) and str(reservation.check_out) > str(check_out)):
                    pass
                else:
                    booked_rooms.append(reservation.room.id)

            rooms = rooms.exclude(id__in=booked_rooms)
        
        if capacity:
            rooms = rooms.filter(capacity__gte=int(capacity))

    context = {
        'rooms': rooms,
        'hotels': hotels,
        
    }
    return render(request, 'rooms/index.html', context)

#booking room page
@login_required(login_url='/')
def book_room_page(request):
    room = Rooms.objects.all().get(id=int(request.GET['roomid']))
    return HttpResponse(render(request,'user/bookroom.html',{'room':room}))


from datetime import datetime  # import datetime class


def handler404(request):
    return render(request, '404.html', status=404)
