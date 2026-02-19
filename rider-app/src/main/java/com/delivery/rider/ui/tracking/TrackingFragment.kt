package com.delivery.rider.ui.tracking

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import com.delivery.rider.R
import com.delivery.rider.ui.viewmodel.TrackingViewModel
import com.google.android.gms.maps.CameraUpdateFactory
import com.google.android.gms.maps.GoogleMap
import com.google.android.gms.maps.OnMapReadyCallback
import com.google.android.gms.maps.SupportMapFragment
import com.google.android.gms.maps.model.LatLng
import com.google.android.gms.maps.model.MarkerOptions
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class TrackingFragment : Fragment(), OnMapReadyCallback {
    
    private val viewModel: TrackingViewModel by viewModels()
    
    private var googleMap: GoogleMap? = null
    private lateinit var tvActiveOrder: TextView
    private lateinit var cardTrackingInfo: MaterialCardView
    private lateinit var tvDistance: TextView
    private lateinit var tvEta: TextView
    private lateinit var btnUpdateStatus: MaterialButton
    
    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View = inflater.inflate(R.layout.fragment_tracking, container, false)
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        tvActiveOrder = view.findViewById(R.id.tvActiveOrder)
        cardTrackingInfo = view.findViewById(R.id.cardTrackingInfo)
        tvDistance = view.findViewById(R.id.tvDistance)
        tvEta = view.findViewById(R.id.tvEta)
        btnUpdateStatus = view.findViewById(R.id.btnUpdateStatus)
        
        val mapFragment = childFragmentManager.findFragmentById(R.id.map) as? SupportMapFragment
        mapFragment?.getMapAsync(this)
        
        observeViewModel()
    }
    
    override fun onMapReady(map: GoogleMap) {
        googleMap = map
        googleMap?.uiSettings?.isZoomControlsEnabled = true
        googleMap?.uiSettings?.isCompassEnabled = true
        
        // Default to Accra, Ghana
        val accra = LatLng(5.6037, -0.1870)
        googleMap?.moveCamera(CameraUpdateFactory.newLatLngZoom(accra, 13f))
        
        updateMapWithTracking()
    }
    
    private fun observeViewModel() {
        viewModel.currentOrder.observe(viewLifecycleOwner) { order ->
            order?.let {
                tvActiveOrder.text = "Order #${it.id.take(8)} • ${it.status.uppercase()}"
                cardTrackingInfo.visibility = View.VISIBLE
                updateMapWithTracking()
            } ?: run {
                tvActiveOrder.text = getString(R.string.tracking_no_order)
                cardTrackingInfo.visibility = View.GONE
            }
        }
        
        viewModel.currentLocation.observe(viewLifecycleOwner) { location ->
            location?.let {
                val riderLatLng = LatLng(it.latitude, it.longitude)
                googleMap?.let { map ->
                    map.clear()
                    map.addMarker(
                        MarkerOptions().position(riderLatLng).title("Your Location")
                    )
                    
                    viewModel.currentOrder.value?.let { order ->
                        map.addMarker(
                            MarkerOptions()
                                .position(LatLng(order.pickupLat, order.pickupLng))
                                .title("Pickup")
                                .snippet(order.pickupAddress)
                        )
                        map.addMarker(
                            MarkerOptions()
                                .position(LatLng(order.dropoffLat, order.dropoffLng))
                                .title("Drop-off")
                                .snippet(order.dropoffAddress)
                        )
                    }
                    
                    map.animateCamera(CameraUpdateFactory.newLatLngZoom(riderLatLng, 15f))
                }
            }
        }
        
        viewModel.distanceToDestination.observe(viewLifecycleOwner) { distance ->
            tvDistance.text = "${distance} km"
            // Rough ETA: 30 km/h average
            val distVal = distance.toFloatOrNull() ?: 0f
            val etaMins = (distVal / 30f * 60f).toInt()
            tvEta.text = if (etaMins > 0) "${etaMins} min" else "--"
        }
    }
    
    private fun updateMapWithTracking() {
        viewModel.startTracking()
    }
}
