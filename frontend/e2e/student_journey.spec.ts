import { test, expect } from '@playwright/test';

test.describe('LearnAI Comprehensive End-to-End Suite', () => {

  test('Student Journey: Login, Dashboard, Courses, Quizzes, Recommendations, Study Plan, AI Tutor, Analytics, Logout', async ({ page }) => {
    // 1. Visit Login Page
    await page.goto('/login', { waitUntil: 'domcontentloaded' });
    await expect(page.getByText('LearnAI')).toBeVisible();
    await expect(page.getByText('AI-Powered Personalized Learning & Knowledge Modeling System')).toBeVisible();

    // 2. Click Demo Student
    await page.getByRole('button', { name: /Demo Student/i }).click();

    // 3. Verify Dashboard
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.getByText(/Alex/i).first()).toBeVisible();
    await expect(page.getByText(/Topic Mastery Breakdown/i)).toBeVisible();
    await expect(page.getByText(/Primary Intelligence Recommendation/i)).toBeVisible();
    await expect(page.getByText(/Active Learning Streak/i)).toBeVisible();

    // 4. Open Courses
    await page.getByRole('link', { name: /Courses/i }).first().click();
    await expect(page).toHaveURL(/.*courses/);
    await expect(page.getByText(/Course Catalog/i)).toBeVisible();
    await expect(page.getByText(/Python Programming Mastery/i).first()).toBeVisible();

    // 5. Open Course Detail via 'Explore Modules'
    await page.getByRole('link', { name: /Explore Modules/i }).first().click();
    await expect(page).toHaveURL(/.*courses\/\d+/);
    await expect(page.getByText(/Curriculum Syllabus/i)).toBeVisible();
    await expect(page.getByText('Loops & Iteration', { exact: true }).first()).toBeVisible();

    // 6. Open Quizzes
    await page.getByRole('link', { name: /Quizzes/i }).first().click();
    await expect(page).toHaveURL(/.*quizzes/);
    await expect(page.getByText(/Assessment Bank/i)).toBeVisible();
    await expect(page.getByText(/Adaptive Quiz: Python Loops/i)).toBeVisible();

    // 7. Open Explainable Recommendations
    await page.getByRole('link', { name: /Recommendations/i }).first().click();
    await expect(page).toHaveURL(/.*recommendations/);
    await expect(page.getByText(/Explainable Recommendations/i)).toBeVisible();
    // Verify 4-Pillar Explainability
    await expect(page.getByText(/WHAT:/i).first()).toBeVisible();
    await expect(page.getByText(/WHY IS THIS RECOMMENDED/i).first()).toBeVisible();
    await expect(page.getByText(/QUANTITATIVE EVIDENCE/i).first()).toBeVisible();
    await expect(page.getByText(/ACTION:/i).first()).toBeVisible();

    // 8. Open Study Plan & Toggle Task
    await page.getByRole('link', { name: /Study Plan/i }).first().click();
    await expect(page).toHaveURL(/.*study-plan/);
    await expect(page.getByText(/Daily Milestones/i)).toBeVisible();
    // Toggle a study plan item
    await page.getByText(/mins/i).first().click();

    // 9. Open AI Tutor & Chat
    await page.getByRole('link', { name: /AI Tutor/i }).first().click();
    await expect(page).toHaveURL(/.*tutor/);
    await expect(page.getByText(/Socratic Engine/i)).toBeVisible();

    // Send a message to AI Tutor
    const messageInput = page.getByPlaceholder(/Ask a conceptual question/i);
    await messageInput.fill('How does a while loop know when to terminate?');
    await page.locator('button[type="submit"]').click();

    // Verify response arrives
    await expect(page.locator('text=while').first()).toBeVisible({ timeout: 10000 });

    // 10. Open Analytics
    await page.getByRole('link', { name: /Analytics/i }).first().click();
    await expect(page).toHaveURL(/.*analytics/);
    await expect(page.getByText(/Learning Telemetry & Analytics/i)).toBeVisible();
    await expect(page.getByText(/Overall Mastery/i)).toBeVisible();

    // 11. Sign Out
    await page.locator('button[title="Sign Out"]').click();
    await expect(page).toHaveURL(/.*login/);

    // 12. Login Again & Verify Persistence
    await page.getByRole('button', { name: /Demo Student/i }).click();
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.getByText(/Alex/i).first()).toBeVisible();
  });

  test('Admin Flow: Roster, Question Bank, and AI Question Generation', async ({ page }) => {
    // 1. Login as Admin
    await page.goto('/login');
    await page.getByRole('button', { name: /Demo Admin/i }).click();

    // 2. Verify Admin Dashboard
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.getByText(/Ada/i).first()).toBeVisible();

    // 3. Open Admin Portal via Sidebar
    await page.getByRole('link', { name: /Admin Portal/i }).click();
    await expect(page).toHaveURL(/.*admin/);
    await expect(page.getByText(/Educator & Administrator Portal/i)).toBeVisible();
    await expect(page.getByText(/Total Students/i)).toBeVisible();

    // 4. View Cohort Roster
    await page.getByRole('link', { name: /Inspect Student Performance/i }).click();
    await expect(page).toHaveURL(/.*admin\/students/);
    await expect(page.getByText(/Student Cohort Roster/i)).toBeVisible();
    await expect(page.getByText(/student@learnai.dev/i)).toBeVisible();

    // 5. Open Question Bank
    await page.getByRole('link', { name: /Admin Portal/i }).click();
    await page.getByRole('link', { name: /Manage Question Bank/i }).click();
    await expect(page).toHaveURL(/.*admin\/questions/);
    await expect(page.getByText(/Assessment Question Bank/i)).toBeVisible();

    // 6. Generate AI Questions Modal
    await page.getByRole('button', { name: /Generate AI Questions/i }).first().click();
    await expect(page.getByText(/AI Question Synthesizer/i)).toBeVisible();

    // Submit generation inside modal form
    await page.locator('form').getByRole('button', { name: /Generate & Add Questions/i }).click();
    await expect(page.getByText(/Successfully generated and added/i)).toBeVisible({ timeout: 15000 });
  });

  test('Teacher Flow: Instructor Access & Prohibited Admin APIs', async ({ page, request }) => {
    // 1. Login as Teacher
    await page.goto('/login');
    await page.getByRole('button', { name: /Demo Teacher/i }).click();

    // 2. Verify Teacher Profile
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.getByText(/Alan/i).first()).toBeVisible();

    // 3. Teacher can access courses and portal
    await page.getByRole('link', { name: /Courses/i }).first().click();
    await expect(page).toHaveURL(/.*courses/);

    // 4. Verify API security: Student cannot invoke Admin Question Generator
    const studentLogin = await request.post('http://127.0.0.1:8000/api/v1/auth/login', {
      data: { email: 'student@learnai.dev', password: 'student123' }
    });
    const studentData = await studentLogin.json();
    const token = studentData.access_token;

    const forbiddenRes = await request.post('http://127.0.0.1:8000/api/v1/admin/generate-ai-questions', {
      headers: { Authorization: `Bearer ${token}` },
      data: { topic_id: 3, difficulty: 'medium', count: 1, weak_concepts: ['loops'] }
    });
    expect(forbiddenRes.status()).toBe(403);
  });

  test('Failure Scenario: Invalid Credentials Display Clean Error', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', 'nonexistent@learnai.dev');
    await page.fill('input[type="password"]', 'wrongpassword');
    await page.locator('button[type="submit"]').click();

    // Check clear error message appears
    await expect(page.getByText(/(Incorrect|Invalid) email or password/i)).toBeVisible();
    await expect(page).toHaveURL(/.*login/);
  });

  test('Failure Scenario: Protected Route Redirects Unauthenticated User', async ({ page }) => {
    await page.goto('/dashboard');
    // Must redirect to login
    await expect(page).toHaveURL(/.*login/);
  });

});
