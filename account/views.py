from django.shortcuts import render, get_object_or_404, redirect
from account.models import ExchangeProposal, Ad, Category
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages # ДЛЯ УВЕДОМЛЕНИЙ ПОЛЬЗОВАТЕЛЮ
from .forms import AdForm# SearchForm
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q # ДЛЯ ЛОГИЧЕСКИХ ОПЕРАЦИЙ В ORM

@login_required
def create(request):
    if request.method == 'POST':
        form = AdForm(request.POST)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.user = request.user
            ad.save()
            messages.success(request, 'Объявление успешно создано!')
            return redirect('ad_detail', id=ad.id)
    else:
        form = AdForm()
    
    context = {
        'form': form
    }
    return render(request, 'create.html', context)

@login_required
def offers(request, id):
    ad = get_object_or_404(Ad, id=id)
    
    if request.user != ad.user:
        return HttpResponseForbidden("Вы не можете просматривать предложения для этого объявления")
    
    # Базовый запрос с оптимизацией
    proposals = ad.received_proposals.select_related(
        'ad_sender', 
        'ad_sender__user',
        'ad_sender__category'
    ).order_by('-created_at')
    
    # Фильтрация
    status_filter = request.GET.get('status')
    sender_filter = request.GET.get('sender')
    
    if status_filter:
        proposals = proposals.filter(status=status_filter)
    if sender_filter:
        proposals = proposals.filter(ad_sender__user__username__icontains=sender_filter)
    
    context = {
        'ad': ad,
        'proposals': proposals,
        'status_choices': ExchangeProposal.STATUS_CHOICES,
    }
    return render(request, 'offers.html', context)

def ad_list(request):
    ads = Ad.objects.select_related('user', 'category').order_by('-created_at')
    
    # Получаем параметры фильтрации из GET-запроса
    query = request.GET.get('query', '')
    category_id = request.GET.get('category')
    condition = request.GET.get('condition')
    
    # Применяем фильтры
    if query:
        ads = ads.filter(
            Q(id__iexact=query) |
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
    
    if category_id:
        ads = ads.filter(category__id=category_id)
    
    if condition:
        ads = ads.filter(condition=condition)
    
    # Получаем все категории для фильтра
    categories = Category.objects.all()
    
    # Пагинация
    paginator = Paginator(ads, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_query': query,
        'current_category': category_id,
        'current_condition': condition,
        'condition_choices': Ad.CONDITION_CHOICES,
    }
    return render(request, 'list.html', context)

@login_required
def edit(request, id):
    ad = get_object_or_404(Ad, id=id)
    if request.user != ad.user:
        return HttpResponseForbidden('Вы не можете управлять этим обьявлением.') # or smth else
    
    if request.method == 'POST':
        edit_form = AdForm(request.POST, instance=ad)
        if edit_form.is_valid():
            edit_form.save()
            return redirect('ad_detail', id=ad.id)
    else:
        edit_form = AdForm(instance=ad)
    
    context = {
        'edit_form': edit_form,
        }
    return render(request, 'edit.html', context)

# Пользователь не сможет запустить вьюху так как требуется пост, а даже если получится то будет проверка на создателя Ad 
@require_POST
@login_required
def delete(request, id):
    ad = get_object_or_404(Ad, id=id)
    if request.user != ad.user:
        return HttpResponseForbidden('Вы не можете управлять этим обьявлением.') # or smth else
    ad.delete()
    return redirect('ad_list')


@require_GET
def ad_detail(request, id):
    ad = get_object_or_404(
        Ad.objects.select_related('user', 'category')
                .annotate(proposals_count=Count('received_proposals')), # чтобы отдельно в шаблоне запрос для count не делать
        id=id
    )
    can_propose_exchange = False
    user_ads = None
    
    if request.user.is_authenticated and request.user != ad.user:
        has_existing_proposal = ad.received_proposals.filter(
            ad_sender__user=request.user
        ).exists()
        
        if not has_existing_proposal:
            can_propose_exchange = True
            user_ads = Ad.objects.filter(user=request.user).exclude(id=ad.id)
    
    context = {
        'ad': ad,
        'can_propose_exchange': can_propose_exchange,
        'user_ads': user_ads,
        'request': request,
    }
    return render(request, 'ad_detail.html', context)

@login_required
def create_trade(request, ad_receiver_id):
    if request.method == 'POST':
        ad_receiver = get_object_or_404(Ad, id=ad_receiver_id)
        
        if request.user == ad_receiver.user:
            messages.error(request, "Вы не можете предложить обмен на свой же товар")
            return redirect('ad_detail', id=ad_receiver_id)
        
        sender_ad_id = request.POST.get('sender_ad')
        if not sender_ad_id:
            messages.error(request, "Не выбрано объявление для обмена")
            return redirect('ad_detail', id=ad_receiver_id)
        
        ad_sender = get_object_or_404(Ad, id=sender_ad_id, user=request.user)
        
        if ExchangeProposal.objects.filter(ad_sender=ad_sender, ad_receiver=ad_receiver).exists():
            messages.warning(request, "Вы уже отправляли это предложение обмена")
            return redirect('ad_detail', id=ad_receiver_id)
        
        # Создаем предложение с комментарием
        ExchangeProposal.objects.create(
            ad_sender=ad_sender,
            ad_receiver=ad_receiver,
            status='pending',
            comment=request.POST.get('comment', '')  # Добавляем комментарий
        )
        
        messages.success(request, "Предложение обмена успешно отправлено!")
        return redirect('ad_detail', id=ad_receiver_id)
    
    return redirect('ad_detail', id=ad_receiver_id)

#ПРОСТОЯ ЗАЩИТА ЧЕРЕЗ ПОСТ ЧТОБЫ ЧЕРЕЗ ГЕТ НИКТО НИЧЕ НЕ ПРИНЯЛ/ОТКЛОНИЛ
@require_POST
@login_required
def accept_proposal(request, proposal_id):
    proposal = get_object_or_404(ExchangeProposal, id=proposal_id)
    
    if proposal.accept():
        messages.success(request, "Предложение успешно принято!")
    else:
        messages.error(request, "Не удалось принять предложение")
    
    return redirect('ad_detail', id=proposal.ad_receiver.id)

#ПРОСТОЯ ЗАЩИТА ЧЕРЕЗ ПОСТ ЧТОБЫ ЧЕРЕЗ ГЕТ НИКТО НИЧЕ НЕ ПРИНЯЛ/ОТКЛОНИЛ
@require_POST
@login_required
def reject_proposal(request, proposal_id):
    proposal = get_object_or_404(ExchangeProposal, id=proposal_id)
    
    if proposal.reject():
        messages.success(request, "Предложение отклонено")
    else:
        messages.error(request, "Не удалось отклонить предложение")
    
    return redirect('ad_detail', id=proposal.ad_receiver.id)