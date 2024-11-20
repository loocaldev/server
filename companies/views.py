from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Company, CompanyMembership
from .serializers import CompanySerializer, CompanyMembershipSerializer
from django.contrib.auth.models import User
from rest_framework_simplejwt.authentication import JWTAuthentication


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_company(request):
    data = request.data
    serializer = CompanySerializer(data=data)
    if serializer.is_valid():
        company = serializer.save(created_by=request.user)
        CompanyMembership.objects.create(user=request.user, company=company, role='owner', invitation_accepted=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def invite_member(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    if not CompanyMembership.objects.filter(user=request.user, company=company, role='owner').exists():
        return Response({"error": "No tienes permisos para invitar usuarios a esta empresa."}, status=403)

    email = request.data.get('email')
    user = User.objects.filter(email=email).first()

    if not user:
        return Response({"error": "Usuario no registrado."}, status=400)

    membership, created = CompanyMembership.objects.get_or_create(
        user=user,
        company=company,
        defaults={"invited_by": request.user, "role": "member"}
    )
    if not created:
        return Response({"error": "El usuario ya pertenece a la empresa."}, status=400)

    return Response({"message": "Invitación enviada exitosamente."}, status=200)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def accept_invitation(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    membership = get_object_or_404(CompanyMembership, user=request.user, company=company)

    if membership.invitation_accepted:
        return Response({"error": "Ya aceptaste esta invitación."}, status=400)

    membership.invitation_accepted = True
    membership.save()
    return Response({"message": "Invitación aceptada exitosamente."}, status=200)
