import 'package:flutter/material.dart';

import '../../services/services.dart';
import '../../widgets/theme.dart';

class NotificationsScreen extends StatelessWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final announcements = AppConfigService.instance.cached?.announcements ?? const [];
    return Scaffold(
      appBar: AppBar(title: const Text('Notifications')),
      body: announcements.isEmpty
          ? const Center(child: Text('No announcements right now.'))
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                for (final item in announcements)
                  Card(
                    color: AppColors.soft,
                    elevation: 0,
                    margin: const EdgeInsets.only(bottom: 10),
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(item['title']?.toString() ?? '',
                              style: const TextStyle(fontWeight: FontWeight.w700)),
                          const SizedBox(height: 4),
                          Text(item['message']?.toString() ?? '', style: const TextStyle(fontSize: 13)),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
    );
  }
}
