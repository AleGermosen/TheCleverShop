from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile
from store.models import Order
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm

# Create your views here.

@login_required
def profile(request):
    return render(request, 'accounts/profile.html')

@login_required
def profile_edit(request):
    if request.method == 'POST':
        # Update user info
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.email = request.POST.get('email')
        request.user.save()
        
        # Update profile info
        profile = request.user.profile
        profile.phone_number = request.POST.get('phone_number')
        profile.address = request.POST.get('address')
        profile.bio = request.POST.get('bio')
        
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        
        profile.save()
        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/profile_edit.html')

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/order_history.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'accounts/order_detail.html', {'order': order})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to CleverCupid.')
            return redirect('store:home')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})
