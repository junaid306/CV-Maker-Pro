import 'package:flutter/material.dart';

import '../models/models.dart';
import '../services/services.dart';
import '../widgets/common_widgets.dart';
import '../widgets/theme.dart';
import 'ai/ai_tools_screen.dart';
import 'ats/ats_checker_screen.dart';
import 'cv/my_cvs_screen.dart';
import 'profile/profile_screen.dart';
import 'templates/template_gallery_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int tabIndex = 0;
  AppConfigModel? config;

  @override
  void initState() {
    super.initState();
    _loadConfig();
  }

  Future<void> _loadConfig() async {
    final result = await AppConfigService.instance.load();
    if (!mounted) return;
    setState(() => config = result);
    if (result.maintenance) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('The app is in maintenance mode. Some features may be unavailable.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = AuthService.instance.currentUser;
    final pages = [
      _homeTab(),
      const TemplateGalleryScreen(),
      const MyCvsScreen(),
      const AiToolsScreen(),
      const ProfileScreen(),
    ];
    return Scaffold(
      body: pages[tabIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: tabIndex,
        onDestinationSelected: (index) => setState(() => tabIndex = index),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: 'Templates'),
          NavigationDestination(icon: Icon(Icons.description_outlined), selectedIcon: Icon(Icons.description), label: 'My CVs'),
          NavigationDestination(icon: Icon(Icons.auto_fix_high_outlined), selectedIcon: Icon(Icons.auto_fix_high), label: 'AI Tools'),
          NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
      floatingActionButton: tabIndex == 0 && (user == null || user.isGuest)
          ? null
          : FloatingActionButton.extended(
              backgroundColor: AppColors.primary,
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const TemplateGalleryScreen(pickMode: true)),
              ),
              icon: const Icon(Icons.add),
              label: const Text('New CV'),
            ),
    );
  }

  Widget _homeTab() {
    final user = AuthService.instance.currentUser;
    return SafeArea(
      child: RefreshIndicator(
        onRefresh: () async => _loadConfig(),
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        user?.isGuest == true
                            ? 'Guest session'
                            : 'Hi, ${user?.fullName ?? user?.email ?? ''}',
                        style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
                      ),
                      const SizedBox(height: 4),
                      Text('Create professional CVs in minutes.', style: TextStyle(color: AppColors.muted, fontSize: 13)),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            if (user?.isGuest == true)
              GestureDetector(
                onTap: () => showSnack(context, 'Ask the owner to enable account upgrade to keep your CVs.'),
                child: Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.soft,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.info_outline, color: AppColors.primary),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text('You are using a guest session. Data stays linked to this device.',
                            style: TextStyle(fontSize: 13, color: AppColors.dark)),
                      ),
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 20),
            _actionGrid(),
            const SizedBox(height: 20),
            ..._announcements(),
          ],
        ),
      ),
    );
  }

  Widget _actionGrid() {
    final actions = [
      ('Templates', Icons.dashboard_outlined, () => setState(() => tabIndex = 1)),
      ('My CVs', Icons.description_outlined, () => setState(() => tabIndex = 2)),
      ('AI Tools', Icons.auto_fix_high_outlined, () => setState(() => tabIndex = 3)),
      ('ATS Checker', Icons.checklist, () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const AtsCheckerScreen()))),
    ];
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.6,
      children: [
        for (final (label, icon, onTap) in actions)
          InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(14),
            child: Container(
              decoration: BoxDecoration(
                color: AppColors.soft,
                borderRadius: BorderRadius.circular(14),
              ),
              padding: const EdgeInsets.all(14),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(icon, color: AppColors.primary, size: 26),
                  const SizedBox(height: 8),
                  Text(label, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
                ],
              ),
            ),
          ),
      ],
    );
  }

  List<Widget> _announcements() {
    final announcements = config?.announcements ?? [];
    if (announcements.isEmpty) return [];
    return [
      const Text('Announcements', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
      const SizedBox(height: 8),
      for (final item in announcements)
        Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: AppColors.soft,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Text(item['message']?.toString() ?? '', style: const TextStyle(fontSize: 13)),
        ),
    ];
  }
}
