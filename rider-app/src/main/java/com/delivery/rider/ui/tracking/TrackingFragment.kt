package com.delivery.rider.ui.tracking

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.fragment.app.Fragment
import com.delivery.rider.R
import com.delivery.rider.BuildConfig
import com.delivery.rider.ui.viewmodel.TrackingViewModel
import androidx.fragment.app.viewModels
import com.mapbox.maps.MapView
import com.mapbox.maps.MapboxMap
import com.mapbox.maps.Style

// trackers and viewmodel
class TrackingFragment : Fragment() {
    private val viewModel: TrackingViewModel by viewModels()
    private var mapView: MapView? = null
    private var mapboxMap: MapboxMap? = null

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View = inflater.inflate(R.layout.fragment_tracking, container, false)

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupMapView()
        observeViewModel()
    }

    private fun setupMapView() {
        val container = view?.findViewById<android.widget.FrameLayout>(R.id.mapContainer) ?: return
        container.removeAllViews()
        if (BuildConfig.USE_OSM_FALLBACK) {
            val web = WebView(requireContext())
            web.settings.javaScriptEnabled = true
            web.webViewClient = WebViewClient()
            web.loadDataWithBaseURL(null, osmHtml(), "text/html", "utf-8", null)
            container.addView(web)
        } else {
            mapView = MapView(requireContext())
            mapboxMap = mapView?.getMapboxMap()
            mapboxMap?.setStyle(Style.MAPBOX_STREETS) {
                // style loaded
            }
            container.addView(mapView!!)
        }
    }

    private fun osmHtml(): String {
        return """
            <!DOCTYPE html>
            <html>
            <head>
              <meta name=\"viewport\" content=\"initial-scale=1.0, user-scalable=no\" />
              <style>html, body { height:100%; margin:0; padding:0; }</style>
              <link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.css\"/>
              <script src=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.js\"></script>
            </head>
            <body>
              <div id=\"map\" style=\"width:100%;height:100%\"></div>
              <script>
                var map = L.map('map').setView([5.6037, -0.1870], 13);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                  maxZoom: 19
                }).addTo(map);
              </script>
            </body>
            </html>
        """.trimIndent()
    }

    private fun observeViewModel() {
        // view model observers can be added here if needed
    }
}
