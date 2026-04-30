from django.shortcuts import render

def redeem_hadiah(request):
    return render(request, 'member/redeem-hadiah.html')

def beli_package(request):
    return render(request, 'member/beli-package.html')

def info_tier(request):
    return render(request, 'member/info-tier.html')

def transfer_miles(request):
    return render(request, 'member/transfer-miles.html')

def claim_member(request):
    return render(request, 'member/claim-member.html')