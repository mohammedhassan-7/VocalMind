import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router'

import { AgentCallDetail } from '../app/components/agent/AgentCallDetail'

const { getInteractionDetailMock, getAudioUrlMock } = vi.hoisted(() => ({
    getInteractionDetailMock: vi.fn(),
    getAudioUrlMock: vi.fn(),
}))

const mockPlay = vi.fn(() => Promise.resolve())

vi.mock('../app/services/api', () => ({
    getInteractionDetail: getInteractionDetailMock,
    getAudioUrl: getAudioUrlMock,
}))

vi.mock('recharts', () => ({
    ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
    CartesianGrid: () => null,
    Tooltip: () => null,
    Legend: () => null,
    XAxis: () => null,
    YAxis: () => null,
    ReferenceLine: () => null,
    Line: () => null,
    LineChart: ({ children }: any) => <div data-testid="emotion-chart">{children}</div>,
    Bar: ({ name }: any) => <div>{name}</div>,
    BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
}))

const makeDetail = ({
    id,
    policyTitle,
    llmTriggers = null,
    audioFilePath = null,
    emotionEvents = [],
    utterances,
}: {
    id: string
    policyTitle?: string
    llmTriggers?: any
    audioFilePath?: string | null
    emotionEvents?: any[]
    utterances?: any[]
}) => ({
    interaction: {
        id,
        agentName: 'Agent A',
        agentId: 'agent-1',
        date: '2025-03-01',
        time: '09:14 AM',
        duration: '4:20',
        language: 'en',
        overallScore: 85,
        empathyScore: 85,
        policyScore: 85,
        resolutionScore: 85,
        resolved: true,
        hasViolation: Boolean(policyTitle),
        hasOverlap: false,
        responseTime: '1.2s',
        status: 'completed',
        audioFilePath,
    },
    utterances:
        utterances ?? [
            {
                id: 'u1',
                interactionId: id,
                speaker: 'agent',
                text: 'Good morning!',
                startTime: 0,
                endTime: 2,
                timestamp: '00:00',
                emotion: 'happy',
                confidence: 0.9,
            },
        ],
    emotionEvents,
    policyViolations: policyTitle
        ? [
              {
                  id: 'v1',
                  interactionId: id,
                  policyName: 'hold_time_limit',
                  policyTitle,
                  category: 'operations',
                  description: 'desc',
                  reasoning: 'reason',
                  severity: 'medium',
                  score: 45,
              },
          ]
        : [],
    emotionComparison: {
        totalUtterances: 1,
        distributions: { acoustic: [], text: [], fused: [] },
        quality: {
            acousticTextAgreementRate: 0,
            fusedMatchesAcousticRate: 0,
            fusedMatchesTextRate: 0,
            disagreementCount: 0,
        },
    },
    llmTriggers,
})

const renderWithId = (id: string) =>
    render(
        <MemoryRouter initialEntries={[`/agent/calls/${id}`]}>
            <Routes>
                <Route path="/agent/calls/:id" element={<AgentCallDetail />} />
            </Routes>
        </MemoryRouter>
    )

describe('AgentCallDetail', () => {
    beforeEach(() => {
        getInteractionDetailMock.mockReset()
        getAudioUrlMock.mockReset()
        mockPlay.mockClear()
        getAudioUrlMock.mockImplementation((id: string) => `/audio/${id}.mp3`)

        Object.defineProperty(HTMLMediaElement.prototype, 'play', {
            configurable: true,
            value: mockPlay,
        })
    })

    it('shows an error state when the interaction cannot be loaded', async () => {
        getInteractionDetailMock.mockRejectedValue(new Error('backend offline'))

        renderWithId('int-404')

        expect(await screen.findByText('Failed to load call details')).toBeInTheDocument()
        expect(screen.getByText('backend offline')).toBeInTheDocument()
    })

    it('renders policy violations in the Policy tab when violations exist', async () => {
        getInteractionDetailMock.mockResolvedValue(makeDetail({ id: 'int-002', policyTitle: 'Hold Time Limit' }))

        renderWithId('int-002')

        // Wait for render, then click Policy tab
        const policyTab = await waitFor(() =>
            screen.getAllByRole('button').find(b => b.textContent?.trim() === 'Policy')
        )
        expect(policyTab).toBeTruthy()
        fireEvent.click(policyTab!)
        expect(await screen.findByText('Hold Time Limit')).toBeInTheDocument()
        expect(screen.getByText('1.2s')).toBeInTheDocument()
        expect(screen.queryByText('1.2ss')).not.toBeInTheDocument()
    })

    it('renders tabbed analysis with process and policy data when llm triggers available', async () => {
        getInteractionDetailMock.mockResolvedValue(
            makeDetail({
                id: 'int-003',
                llmTriggers: {
                    available: true,
                    processAdherence: {
                        detectedTopic: 'billing_issue',
                        isResolved: false,
                        efficiencyScore: 6,
                        justification: 'Agent missed one verification step.',
                        missingSopSteps: ['Confirm account details'],
                    },
                    nliPolicy: {
                        nliCategory: 'Contradiction',
                        justification: 'Agent statement conflicts with policy.',
                    },
                },
            })
        )

        renderWithId('int-003')

        // Should show tabbed analysis — click Process tab
        const processTab = await waitFor(() =>
            screen.getAllByRole('button').find(b => b.textContent?.trim() === 'Process')
        )
        expect(processTab).toBeTruthy()
        fireEvent.click(processTab!)
        expect(await screen.findByText(/Call Flow Check/)).toBeInTheDocument()
        expect(screen.getByText('billing_issue')).toBeInTheDocument()

        // Click Policy tab
        const policyTab = screen.getAllByRole('button').find(b => b.textContent?.trim() === 'Policy')
        fireEvent.click(policyTab!)
        expect(await screen.findByText(/Policy Consistency/)).toBeInTheDocument()
        expect(screen.getByText('Contradiction')).toBeInTheDocument()
    })

    it('renders the audio player and seeks to the selected emotion event', async () => {
        getInteractionDetailMock.mockResolvedValue(
            makeDetail({
                id: 'int-005',
                audioFilePath: 'recordings/int-005.mp3',
                emotionEvents: [
                    {
                        id: 'e1',
                        interactionId: 'int-005',
                        fromEmotion: 'neutral',
                        toEmotion: 'happy',
                        timestamp: '00:05',
                        jumpToSeconds: 5,
                        justification: 'Customer relaxed after the explanation.',
                    },
                ],
            })
        )

        renderWithId('int-005')

        // Wait for component to render fully
        expect(await screen.findByText('Emotion Timeline')).toBeInTheDocument()
        const audio = document.querySelector('audio') as HTMLAudioElement | null
        expect(audio).not.toBeNull()
        Object.defineProperty(audio!, 'currentTime', {
            configurable: true,
            writable: true,
            value: 0,
        })

        expect(audio).toHaveAttribute('src', '/audio/int-005.mp3')
        expect(getAudioUrlMock).toHaveBeenCalledWith('int-005')

        // Find and click the play button for the emotion event
        const playButtons = await screen.findAllByRole('button')
        const jumpBtn = playButtons.find(b => b.textContent?.includes('00:05'))
        expect(jumpBtn).toBeTruthy()
        fireEvent.click(jumpBtn!)

        expect(audio!.currentTime).toBe(5)
        expect(mockPlay).toHaveBeenCalledTimes(1)
    })

    it('falls back to a neutral transcript label for unknown emotions', async () => {
        getInteractionDetailMock.mockResolvedValue(
            makeDetail({
                id: 'int-006',
                utterances: [
                    {
                        id: 'u1',
                        interactionId: 'int-006',
                        speaker: 'agent',
                        text: 'I can help with that.',
                        startTime: 0,
                        endTime: 2,
                        timestamp: '00:00',
                        emotion: 'happy',
                        confidence: 0.9,
                    },
                    {
                        id: 'u2',
                        interactionId: 'int-006',
                        speaker: 'customer',
                        text: 'I am not sure this is working.',
                        startTime: 3,
                        endTime: 5,
                        timestamp: '00:03',
                        emotion: 'mystery',
                        confidence: 0.53,
                    },
                ],
            })
        )

        renderWithId('int-006')

        expect(await screen.findByText('Transcript')).toBeInTheDocument()
        expect(screen.getByText('Me')).toBeInTheDocument()
        expect(screen.getAllByText('Customer').length).toBeGreaterThan(0)
        expect(screen.getByText('Neutral 53%')).toBeInTheDocument()
    })

    it('fetches llm-enriched data with includeLLMTriggers flag', async () => {
        getInteractionDetailMock.mockResolvedValue(
            makeDetail({
                id: 'int-007',
                llmTriggers: {
                    available: true,
                    processAdherence: {
                        detectedTopic: 'billing_issue',
                        isResolved: false,
                        efficiencyScore: 6,
                        justification: 'Initial pass.',
                        missingSopSteps: [],
                    },
                },
            })
        )

        renderWithId('int-007')

        await waitFor(() => {
            expect(getInteractionDetailMock).toHaveBeenCalledWith('int-007', {
                includeLLMTriggers: true,
                skipCache: true,
            })
        })
        // Agent view should not have a Reprocess button
        expect(screen.queryByRole('button', { name: /Reprocess/i })).not.toBeInTheDocument()
    })
})
