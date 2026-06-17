describe('Manager Settings', () => {
  beforeEach(() => {
    cy.visitAs('manager', '/manager/settings');
  });

  it('renders the manager settings page with default profile tab', () => {
    cy.contains('h2', 'Settings & Preferences').should('be.visible');
    cy.contains('h3', 'Profile Information').should('be.visible');
    cy.get('input[type="email"]').should('have.value', 'manager@vocalmind.ai');
    cy.get('input[type="text"]').first().should('have.value', 'Manager King');
  });

  it('switches between tabs and displays the correct content', () => {
    // Notifications tab
    cy.contains('button', 'Notifications').click();
    cy.contains('h3', 'Notification Preferences').should('be.visible');
    cy.contains('delivered to the bell').should('be.visible');

    // Security tab (functional password form)
    cy.contains('button', 'Privacy & Security').click();
    cy.contains('h3', 'Privacy & Security').should('be.visible');
    cy.contains('label', 'New Password').should('be.visible');
    cy.contains('button', 'Change Password').should('be.visible');

    // API Keys tab
    cy.contains('button', 'API Keys').click();
    cy.contains('h3', 'API Keys').should('be.visible');
    cy.contains('Generate and revoke').should('be.visible');

    // Back to Profile
    cy.contains('button', 'Profile').click();
    cy.contains('h3', 'Profile Information').should('be.visible');
  });
});
