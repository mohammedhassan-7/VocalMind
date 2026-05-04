describe('Agent Calls List', () => {
  it('renders the page header and summary stats', () => {
    cy.visitAs('agent', '/agent/calls');
    cy.contains('MY CALLS').should('be.visible');
    cy.contains('Review recent conversations').should('be.visible');
    cy.contains('Total').should('be.visible');
    cy.contains('Completed').should('be.visible');
    cy.contains('Need Review').should('be.visible');
  });

  it('renders call cards with date, score, and status', () => {
    cy.visitAs('agent', '/agent/calls');
    cy.get('a[href^="/agent/calls/"]').should('have.length.at.least', 1);
    cy.get('a[href^="/agent/calls/"]').first().within(() => {
      cy.contains(/\d{4}-\d{2}-\d{2}/).should('exist');
      cy.contains(/\d+%/).should('exist');
      cy.contains(/Resolved|Unresolved/).should('exist');
    });
  });

  it('shows violation badges on flagged calls', () => {
    cy.visitAs('agent', '/agent/calls');
    cy.contains('Review needed').should('exist');
  });

  it('navigates to call detail when a card is clicked', () => {
    cy.visitAs('agent', '/agent/calls');
    cy.get('a[href^="/agent/calls/"]').first().click();
    cy.location('pathname').should('match', /\/agent\/calls\/.+/);
  });

  it('shows an error state when the API fails', () => {
    cy.visitAs('agent', '/agent/calls', {
      interactions: { statusCode: 500 },
    });
    cy.contains('Failed to load calls').should('be.visible');
  });

  it('shows an empty state when there are no calls', () => {
    cy.visitAs('agent', '/agent/calls', {
      interactions: { body: [] },
    });
    cy.contains('No calls yet').should('be.visible');
  });
});
