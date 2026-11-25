import 'package:flutter/material.dart';

import '../../services/services.dart';
import '../../widgets/common_widgets.dart';
import '../../widgets/theme.dart';
import '../dashboard_screen.dart';

class SignUpScreen extends StatefulWidget {
  const SignUpScreen({super.key});

  @override
  State<SignUpScreen> createState() => _SignUpScreenState();
}

class _SignUpScreenState extends State<SignUpScreen> {
  final email = TextEditingController();
  final fullName = TextEditingController();
  final password = TextEditingController();
  bool loading = false;
  String? error;

  Future<void> submit() async {
    if (password.text.length < 8) {
      setState(() => error = 'Password must be at least 8 characters.');
      return;
    }
    setState(() {
      loading = true;
      error = null;
    });
    try {
      await AuthService.instance.register(email.text.trim(), password.text, fullName.text.trim());
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
      appBar: AppBar(title: const Text('Create account')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          AppTextField(controller: fullName, label: 'Full name'),
          const SizedBox(height: 12),
          AppTextField(controller: email, label: 'Email', keyboardType: TextInputType.emailAddress),
          const SizedBox(height: 12),
          AppTextField(controller: password, label: 'Password', obscure: true, hint: 'At least 8 characters'),
          if (error != null) ...[
            const SizedBox(height: 12),
            Text(error!, style: const TextStyle(color: AppColors.danger, fontSize: 13)),
          ],
          const SizedBox(height: 20),
          PrimaryButton(label: 'Sign up', onPressed: submit, loading: loading),
        ],
      ),
    );
  }
}
