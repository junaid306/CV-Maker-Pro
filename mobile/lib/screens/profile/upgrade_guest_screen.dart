import 'package:flutter/material.dart';

import '../../services/services.dart';
import '../../widgets/common_widgets.dart';
import '../../widgets/theme.dart';
import '../dashboard_screen.dart';

class UpgradeGuestScreen extends StatefulWidget {
  const UpgradeGuestScreen({super.key});

  @override
  State<UpgradeGuestScreen> createState() => _UpgradeGuestScreenState();
}

class _UpgradeGuestScreenState extends State<UpgradeGuestScreen> {
  final email = TextEditingController();
  final fullName = TextEditingController();
  final password = TextEditingController();
  bool loading = false;
  String? error;

  Future<void> submit() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      await AuthService.instance.upgradeGuest(email.text.trim(), password.text, fullName.text.trim());
      if (!mounted) return;
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const DashboardScreen()),
        (route) => false,
      );
    } catch (e) {
      setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Upgrade guest account')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          const Text(
            'All of your existing CVs, credits and rewards will be preserved and moved to your new account.',
            style: TextStyle(fontSize: 13),
          ),
          const SizedBox(height: 16),
          AppTextField(controller: fullName, label: 'Full name'),
          const SizedBox(height: 12),
          AppTextField(controller: email, label: 'Email', keyboardType: TextInputType.emailAddress),
          const SizedBox(height: 12),
          AppTextField(controller: password, label: 'Password', obscure: true),
          if (error != null) ...[
            const SizedBox(height: 12),
            Text(error!, style: const TextStyle(color: AppColors.danger, fontSize: 13)),
          ],
          const SizedBox(height: 20),
          PrimaryButton(label: 'Upgrade account', onPressed: submit, loading: loading),
        ],
      ),
    );
  }
}
