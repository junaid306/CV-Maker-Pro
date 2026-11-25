import 'package:flutter/material.dart';

import '../../services/services.dart';
import '../../widgets/theme.dart';
import '../ai/rewards_screen.dart';
import '../auth/login_screen.dart';
import '../splash_screen.dart';
import 'upgrade_guest_screen.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final user = AuthService.instance.currentUser;
    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Row(
            children: [
              CircleAvatar(
                backgroundColor: AppColors.primary,
                child: Text(
                  (user?.fullName ?? user?.email ?? 'G').isNotEmpty
                      ? (user?.fullName ?? user?.email ?? 'G')[0].toUpperCase()
                      : 'G',
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(user?.fullName ?? 'Guest user',
                        style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                    Text(user?.email ?? 'Temporary session',
                        style: TextStyle(fontSize: 12, color: AppColors.muted)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          if (user?.isGuest == true)
            ListTile(
              leading: const Icon(Icons.upgrade, color: AppColors.primary),
              title: const Text('Upgrade guest account'),
              subtitle: const Text('Keep your CVs with a real account'),
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const UpgradeGuestScreen()),
              ),
            ),
          ListTile(
            leading: const Icon(Icons.card_giftcard, color: AppColors.primary),
            title: const Text('Ads & rewards'),
            subtitle: const Text('Export unlock progress'),
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const RewardsScreen(purpose: 'export')),
            ),
          ),
          ListTile(
            leading: const Icon(Icons.logout, color: AppColors.danger),
            title: const Text('Log out'),
            onTap: () async {
              await AuthService.instance.logout();
              if (!context.mounted) return;
              Navigator.of(context).pushAndRemoveUntil(
                MaterialPageRoute(builder: (_) => const SplashScreen()),
                (route) => false,
              );
            },
          ),
          const SizedBox(height: 12),
          TextButton(
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const LoginScreen()),
            ),
            child: const Text('Switch account'),
          ),
        ],
      ),
    );
  }
}
