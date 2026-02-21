package com.mapbox.maps

class MapboxMap {
    fun setStyle(style: String, callback: (Style) -> Unit) {
        callback(Style())
    }
}
