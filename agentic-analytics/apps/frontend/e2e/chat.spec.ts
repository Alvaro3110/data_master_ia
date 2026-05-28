import { test, expect } from '@playwright/test';

test.describe('ChatPanel E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept the initial POST to start the stream
    await page.route('**/api/v1/ask-analytics/stream', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          trace_id: 'fake-trace-123',
          data: { trace_id: 'fake-trace-123' },
        }),
      });
    });

    // Intercept the EventSource GET request
    await page.route('**/api/v1/ask-analytics/stream/fake-trace-123*', async (route) => {
      // Simulate an SSE stream with proper event types
      const ssePayload = 
        `event: start\n` +
        `data: {"trace_id": "fake-trace-123"}\n\n` +
        `event: chunk\n` +
        `data: {"text": "Hello"}\n\n` +
        `event: chunk\n` +
        `data: {"text": " World!"}\n\n` +
        `event: done\n` +
        `data: {"answer": "Hello World!"}\n\n`;

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: ssePayload,
      });
    });

    await page.goto('/');
  });

  test('should render chat input, submit message, and display streaming response', async ({ page }) => {
    // Find the input box
    const input = page.getByPlaceholder(/Pergunte sobre/i);
    await expect(input).toBeVisible();

    // Type a message
    await input.fill('Qual a margem da safra 2026?');

    // Click submit
    const submitBtn = page.getByRole('button', { name: /enviar/i });
    await submitBtn.click();

    // Verify user message appears
    await expect(page.getByText('Qual a margem da safra 2026?')).toBeVisible();

    // Verify assistant's streaming response appears
    await expect(page.getByText('Hello World!')).toBeVisible();
  });
});
