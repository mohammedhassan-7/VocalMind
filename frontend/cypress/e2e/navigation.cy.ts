describe('Sidebar and cross-page navigation', () => {
  it('collapses and expands the manager sidebar', () => {
    cy.loginAs('manager');
    cy.contains('Average Score').should('be.visible');

    // Sidebar starts expanded — nav labels should be visible
    cy.get('nav[aria-label="Manager navigation"]')
      .contains('Session Inspector').should('exist');

    // Collapse
    cy.get('[data-cy="sidebar-collapse-toggle"]').click();
    cy.get('nav[aria-label="Manager navigation"]')
      .contains('Session Inspector').should('not.exist');

    // Expand
    cy.get('[data-cy="sidebar-collapse-toggle"]').click();
    cy.get('nav[aria-label="Manager navigation"]')
      .contains('Session Inspector').should('exist');
  });

  it('collapses and expands the agent sidebar', () => {
    cy.loginAs('agent');
    cy.contains('My Performance').should('be.visible');

    // Sidebar starts expanded
    cy.get('nav').contains('My Calls').should('exist');

    // Collapse
    cy.get('[data-cy="sidebar-collapse-toggle"]').click();
    cy.get('nav').contains('My Calls').should('not.exist');

    // Expand
    cy.get('[data-cy="sidebar-collapse-toggle"]').click();
    cy.get('nav').contains('My Calls').should('exist');
  });

  it('navigates between agent pages via the sidebar', () => {
    cy.loginAs('agent');
    cy.contains('My Performance').should('be.visible');

    cy.get('nav').contains('My Calls').click();
    cy.location('pathname').should('eq', '/agent/calls');
    cy.contains('MY CALLS').should('be.visible');

    cy.get('nav').contains('My Performance').click();
    cy.location('pathname').should('eq', '/agent');
    cy.contains('Overall Score').should('be.visible');
  });

  it('navigates through the full manager flow via sidebar', () => {
    cy.loginAs('manager');
    cy.contains('Average Score').should('be.visible');

    cy.get('nav[aria-label="Manager navigation"]')
      .contains('Session Inspector').click();
    cy.location('pathname').should('eq', '/manager/inspector');
    cy.contains('h1', 'Session Inspector').should('be.visible');

    cy.get('nav[aria-label="Manager navigation"]')
      .contains('Manager Assistant').click();
    cy.location('pathname').should('eq', '/manager/assistant');

    cy.get('nav[aria-label="Manager navigation"]')
      .contains('Knowledge Base').click();
    cy.location('pathname').should('eq', '/manager/knowledge');
    cy.contains('Knowledge Engine').should('be.visible');

    cy.get('nav[aria-label="Manager navigation"]')
      .contains('Dashboard').click();
    cy.location('pathname').should('eq', '/manager');
    cy.contains('Average Score').should('be.visible');
  });

  it('renders the agent settings page with user info', () => {
    cy.loginAs('agent');
    cy.contains('My Performance').should('be.visible');

    cy.get('[data-cy="user-menu-trigger"]').click();
    cy.contains('Settings').click();

    cy.location('pathname').should('eq', '/agent/settings');
    cy.contains('Account Settings').should('be.visible');
    cy.contains('Robert King').should('be.visible');
  });

  it('filters interactions in the session inspector search', () => {
    cy.visitAs('manager', '/manager/inspector');
    cy.contains('Sarah M.').should('be.visible');

    cy.get('input[placeholder="Search agent, date, ID…"]').type('Sarah');
    cy.contains('Sarah M.').should('be.visible');
    cy.contains('John D.').should('not.exist');

    cy.get('input[placeholder="Search agent, date, ID…"]').clear();
    cy.contains('Sarah M.').should('be.visible');
    cy.contains('John D.').should('be.visible');
  });
});
