from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .models import GatePass, checkin, event


class VerifyPassApiTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="tester", password="secret123")
		self.client.login(username="tester", password="secret123")

		self.event = event.objects.create(name="Sample Event", category="external")
		self.gate_pass = GatePass.objects.create(
			pass_number="123456",
			holder_name="Test User",
			event=self.event,
			valid_until=timezone.localdate() + timedelta(days=1),
		)

	def test_verify_pass_returns_details(self):
		checkin.objects.create(holder=self.gate_pass, checkin_members=1)

		response = self.client.get(reverse("verify_pass_api", args=[self.gate_pass.pass_number]))

		self.assertEqual(response.status_code, 200)
		data = response.json()
		self.assertTrue(data["verified"])
		self.assertEqual(data["pass"]["pass_number"], self.gate_pass.pass_number)
		self.assertEqual(data["pass"]["event"]["name"], self.event.name)
		self.assertTrue(data["verification"]["is_checked_in"])
		self.assertEqual(data["verification"]["checkin_count"], 1)

	def test_verify_pass_without_parameter_returns_400(self):
		response = self.client.get(reverse("verify_pass_api_query"))
		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.json()["verified"], False)

	def test_verify_pass_not_found_returns_404(self):
		response = self.client.get(reverse("verify_pass_api", args=["999999"]))
		self.assertEqual(response.status_code, 404)
		self.assertEqual(response.json()["verified"], False)
