from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from .serializers import (
    OrderCreateSerializer, 
    OrderSimpliedSerializer, 
    OrderDetailSerializer,
    OrderStatusUpdateSerializer,
    OrderCanceledByCustomerSerializer
)
from ..models import Order

# Create your views here.

class CustomerOrderViewSet(viewsets.ModelViewSet):
    """
    Viewset for users to manage orders
681
    Endpoints:
    - POST /users/{username}/orders/ - Create new order
    - GET /users/{username}/orders/ - List user's orders
    - GET /users/{username}/orders/{id}/ - Get order detail
    - POST /users/{username}/orders/{id}/cancel/ - Cancel order
    - GET / users/{username}/orders/statistics - List stats
    """

    permission_classes = [IsAuthenticated]
    lookup_field = "username"

    def get_user(self):
        """Get user from URL parameter"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        username = self.kwargs.get("username")
        return get_object_or_404(User, username=username)

    def get_queryset(self):
        """Return orders for the specific user from URL"""
        user = self.get_user()
        # Query to look up user's past orders
        queryset = Order.objects.filter(user=user).annotate(
            item_count=Count("items")
        ).select_related("user").prefetch_related("items__item")

        return queryset.order_by("-created_at")
    
    def get_serializer_class(self):
        """Return proper serializers based on specific actions"""
        if self.action == "create":
            return OrderCreateSerializer
        elif self.action == "retrieve":
            return OrderDetailSerializer
        elif self.action == "cancel":
            return OrderCanceledByCustomerSerializer
        else:
            return OrderSimpliedSerializer
        
    def create(self, request, *args, **kwargs):
        user = self.get_user()

        # The user can only order for themselves
        if not request.user.is_staff and request.user != user:
            return Response(
                {"detail": "You can only create orders for yourself"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        # Verify the order was created for the correct user
        if order.user != user:
            order.delete()
            return Response(
                {"detail": "Order's user mismatches with current user"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return detailed order information
        detail_serializer = OrderDetailSerializer(order)

        return Response(
            detail_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    def list(self, request, *args, **kwargs):
        """List orders for the specific user"""

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Get detailed order information"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=["GET"])
    def statistics(self, request, *args, **kwargs):
        """
        Get order statistics for the specific user
        
        Only returns counts by status
        """
        user = self.get_user()

        # Only can retrieve the stats for their own accounts
        if not request.user.is_staff and request.user != user:
            return Response(
                {"detail": "You can only view your own statistics"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = Order.objects.filter(user=user)

        stats = {
            'total': queryset.count(),
            'pending': queryset.filter(status=Order.Status.PENDING).count(),
            'ready': queryset.filter(status=Order.Status.READY).count(),
            'complete': queryset.filter(status=Order.Status.COMPLETE).count(),
            'canceled': queryset.filter(status=Order.Status.CANCELED).count(),
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, *args, **kwargs):
        """
        Cancel order by customer
        
        Required field:
        - cancel_reason: Reason for cancellation
        """
        instance = self.get_object()
        user = self.get_user()
        
        # Ensure order belongs to the user in the URL
        if instance.user != user:
            return Response(
                {'detail': 'Order does not belong to this user'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Ensure user can only cancel their own orders (unless staff)
        if not request.user.is_staff and instance.user != request.user:
            return Response(
                {'detail': 'You can only cancel your own orders'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(
            data=request.data,
            context={'order': instance}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Return updated order information
        detail_serializer = OrderDetailSerializer(order)
        return Response(detail_serializer.data)
    

class StaffOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for staff order management
    
    Staff endpoints:
    - GET /staff/orders/ - List all orders (with filters)
    - GET /staff/orders/{id}/ - Get order detail
    - PATCH /staff/orders/{id}/ - Update order status (direct update)
    - PATCH /staff/orders/{id}/update-status/ - Update order status (custom action)
    - GET /staff/orders/statistics/ - Get overall statistics
    """
    permission_classes = [IsAdminUser]
    http_method_names = ['get', 'patch', 'head', 'options']  # Only allow GET and PATCH
    
    def get_queryset(self):
        """
        Return all orders with annotations
        """
        queryset = Order.objects.all().annotate(
            item_count=Count('items')
        ).select_related('user').prefetch_related('items__item')
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return OrderDetailSerializer
        elif self.action in ['update', 'partial_update', 'update_status']:
            return OrderStatusUpdateSerializer
        else:
            return OrderSimpliedSerializer
    
    def list(self, request, *args, **kwargs):
        """
        List all orders with filtering options
        
        Query params:
        - status: Filter by status (pending, ready, complete, canceled)
        - date_from: Filter orders from date (YYYY-MM-DD)
        - date_to: Filter orders to date (YYYY-MM-DD)
        - search: Search by user name or phone
        """
        queryset = self.get_queryset()
        
        # Status filter
        status_filter = request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Date range filter
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        if date_from:
            try:
                date_from_obj = timezone.datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = timezone.datetime.strptime(date_to, '%Y-%m-%d')
                # Include the entire day
                date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
                queryset = queryset.filter(created_at__lte=date_to_obj)
            except ValueError:
                pass
        
        # Search filter (user name or phone)
        search = request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__phone__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Get detailed order information
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        """
        Update order status
        
        Valid transitions:
        - PENDING -> READY or CANCELED
        - READY -> COMPLETE or CANCELED
        """
        instance = self.get_object()
        
        # Get cancel reason if status is being changed to canceled
        cancel_reason = request.data.get('cancel_reason', 'Canceled by staff')
        
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True,
            context={'cancel_reason': cancel_reason}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return detailed order information
        detail_serializer = OrderDetailSerializer(instance)
        return Response(detail_serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get overall order statistics
        
        Query params:
        - date: Specific date (YYYY-MM-DD) - defaults to today
        - date_from: Start date for date range (YYYY-MM-DD)
        - date_to: End date for date range (YYYY-MM-DD)
        - period: Predefined periods (today, yesterday, week, month, year)
        
        Examples:
        - /staff/orders/statistics/ → Today's stats
        - /staff/orders/statistics/?date=2024-11-01 → Specific date
        - /staff/orders/statistics/?period=yesterday → Yesterday's stats
        - /staff/orders/statistics/?period=week → Last 7 days
        - /staff/orders/statistics/?date_from=2024-11-01&date_to=2024-11-30 → Custom range
        """
        from datetime import timedelta
        
        queryset = Order.objects.all()
        today = timezone.now().date()
        
        # Handle predefined periods
        period = request.query_params.get('period', None)
        if period:
            if period == 'today':
                start_date = today
                end_date = today
            elif period == 'yesterday':
                start_date = today - timedelta(days=1)
                end_date = today - timedelta(days=1)
            elif period == 'week':
                start_date = today - timedelta(days=7)
                end_date = today
            elif period == 'month':
                start_date = today - timedelta(days=30)
                end_date = today
            elif period == 'year':
                start_date = today - timedelta(days=365)
                end_date = today
            else:
                return Response(
                    {'error': 'Invalid period. Use: today, yesterday, week, month, or year'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            queryset = queryset.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )
            period_label = period
        
        # Handle specific date
        elif request.query_params.get('date'):
            date_str = request.query_params.get('date')
            try:
                specific_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date=specific_date)
                start_date = specific_date
                end_date = specific_date
                period_label = date_str
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Handle date range
        elif request.query_params.get('date_from') or request.query_params.get('date_to'):
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            try:
                if date_from:
                    start_date = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
                    queryset = queryset.filter(created_at__date__gte=start_date)
                else:
                    start_date = None
                
                if date_to:
                    end_date = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
                    queryset = queryset.filter(created_at__date__lte=end_date)
                else:
                    end_date = None
                
                period_label = f"{date_from or 'start'} to {date_to or 'now'}"
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Default to today
        else:
            queryset = queryset.filter(created_at__date=today)
            start_date = today
            end_date = today
            period_label = 'today'
        
        # Calculate statistics
        stats = {
            'period': period_label,
            'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
            'end_date': end_date.strftime('%Y-%m-%d') if end_date else None,
            'total': queryset.count(),
            'pending': queryset.filter(status=Order.Status.PENDING).count(),
            'ready': queryset.filter(status=Order.Status.READY).count(),
            'complete': queryset.filter(status=Order.Status.COMPLETE).count(),
            'canceled': queryset.filter(status=Order.Status.CANCELED).count(),
        }
        
        # Add revenue if orders have total field
        try:
            from django.db.models import Sum
            revenue = queryset.filter(
                status=Order.Status.COMPLETE
            ).aggregate(total_revenue=Sum('total'))['total_revenue']
            stats['revenue'] = float(revenue) if revenue else 0.0
        except:
            pass
        
        return Response(stats)