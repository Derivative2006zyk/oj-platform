package com.ojplatform.app.widget

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.widget.RemoteViews
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.ojplatform.app.MainActivity
import com.ojplatform.app.R
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class OjWidgetWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val context = applicationContext
        val prefs = context.getSharedPreferences(
            "CapacitorStorage",
            Context.MODE_PRIVATE
        )
        val token = prefs.getString("oj_token", null)

        val views = RemoteViews(context.packageName, R.layout.widget_oj)
        setOpenAppIntent(context, views)

        if (token.isNullOrBlank()) {
            views.setTextViewText(R.id.widget_title, "OJ Platform")
            views.setTextViewText(R.id.widget_today, "未登录")
            views.setTextViewText(R.id.widget_rate, "打开 App 登录")
            views.setTextViewText(R.id.widget_solved, "")
            updateAllWidgets(context, views)
            return Result.success()
        }

        val baseUrl = context.getString(R.string.oj_api_base_url)
        val url = "$baseUrl/api/widget/summary"

        return try {
            val client = OkHttpClient.Builder()
                .connectTimeout(5, TimeUnit.SECONDS)
                .readTimeout(5, TimeUnit.SECONDS)
                .build()

            val request = Request.Builder()
                .url(url)
                .addHeader("Authorization", "Bearer $token")
                .build()

            val response = client.newCall(request).execute()
            val body = response.body?.string()

            if (!response.isSuccessful || body.isNullOrBlank()) {
                views.setTextViewText(R.id.widget_title, "OJ Platform")
                views.setTextViewText(R.id.widget_today, "数据获取失败")
                views.setTextViewText(R.id.widget_rate, "")
                views.setTextViewText(R.id.widget_solved, "")
                updateAllWidgets(context, views)
                return Result.success()
            }

            val json = JSONObject(body)
            val todaySubmissions = json.optInt("today_submissions", 0)
            val acceptanceRate = json.optDouble("acceptance_rate", 0.0)
            val solvedProblems = json.optInt("solved_problems", 0)
            val totalProblems = json.optInt("total_problems", 0)

            views.setTextViewText(R.id.widget_title, "OJ Platform")
            views.setTextViewText(R.id.widget_today, "今日提交：$todaySubmissions")
            views.setTextViewText(R.id.widget_rate, "通过率：$acceptanceRate%")
            views.setTextViewText(R.id.widget_solved, "已解：$solvedProblems / $totalProblems")
            updateAllWidgets(context, views)

            Result.success()
        } catch (e: Exception) {
            views.setTextViewText(R.id.widget_title, "OJ Platform")
            views.setTextViewText(R.id.widget_today, "网络异常")
            views.setTextViewText(R.id.widget_rate, "")
            views.setTextViewText(R.id.widget_solved, "")
            updateAllWidgets(context, views)
            Result.success()
        }
    }

    private fun setOpenAppIntent(context: Context, views: RemoteViews) {
        val intent = Intent(context, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            context,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_root, pendingIntent)
    }

    private fun updateAllWidgets(context: Context, views: RemoteViews) {
        val manager = AppWidgetManager.getInstance(context)
        val component = ComponentName(context, OjWidgetProvider::class.java)
        val ids = manager.getAppWidgetIds(component)
        for (id in ids) {
            manager.updateAppWidget(id, views)
        }
    }
}