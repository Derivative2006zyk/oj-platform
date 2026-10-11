package com.ojplatform.app.widget

data class WidgetData(
    val totalSubmissions: Int,
    val todaySubmissions: Int,
    val totalAccepted: Int,
    val acceptanceRate: Double,
    val solvedProblems: Int,
    val totalProblems: Int,
)