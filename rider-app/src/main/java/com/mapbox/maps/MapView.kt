package com.mapbox.maps

import android.content.Context
import android.view.View

class MapView(context: Context): View(context) {
    fun getMapboxMap(): MapboxMap = MapboxMap()
}
