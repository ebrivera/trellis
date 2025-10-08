'use client'

import { useState } from 'react'
import { DebateViewer } from '../../components/ui/DebateViewer'
import { Button } from '../../components/ui/Button'
import type { AgentName, DebateMessage } from '@trellis/types'

export default function DebateTestPage() {
    const [messages, setMessages] = useState<Record<AgentName, DebateMessage[]>>({
        Planner: [],
        Operations: [],
        HumanFlourishing: [],
        Moderator: []
    })
    const [currentRound, setCurrentRound] = useState<1 | 2 | 3>(1)
    const [winner, setWinner] = useState<AgentName | undefined>()
    const [voteTally, setVoteTally] = useState<Record<AgentName, number> | undefined>()

    const addTestProposal = () => {
        setMessages({
            Planner: [{
                round: 1,
                agent: 'Planner',
                messageType: 'proposal',
                content: 'Use capacity-balanced matching to ensure even distribution across all roles.'
            }],
            Operations: [{
                round: 1,
                agent: 'Operations',
                messageType: 'proposal',
                content: 'Focus on volunteer availability and avoid over-scheduling to prevent burnout.'
            }],
            HumanFlourishing: [{
                round: 1,
                agent: 'HumanFlourishing',
                messageType: 'proposal',
                content: 'Prioritize spiritual gifts and relational connections for long-term engagement.'
            }],
            Moderator: []
        })
    }

    const addTestRebuttal = () => {
        setCurrentRound(2)
        setMessages(prev => ({
            Planner: [
                ...prev.Planner,
                {
                    round: 2,
                    agent: 'Planner',
                    messageType: 'rebuttal',
                    content: 'Operations is too cautious. We need to maximize efficiency.'
                }
            ],
            Operations: [
                ...prev.Operations,
                {
                    round: 2,
                    agent: 'Operations',
                    messageType: 'rebuttal',
                    content: 'Planner ignores the human cost of overwork. Sustainability matters.'
                }
            ],
            HumanFlourishing: [
                ...prev.HumanFlourishing,
                {
                    round: 2,
                    agent: 'HumanFlourishing',
                    messageType: 'rebuttal',
                    content: 'Both approaches miss the relational aspect of serving together.'
                }
            ],
            Moderator: []
        }))
    }

    const addTestVoting = () => {
        setCurrentRound(3)
        setMessages(prev => ({
            Planner: [
                ...prev.Planner,
                {
                    round: 3,
                    agent: 'Planner',
                    messageType: 'vote',
                    content: 'Voted for Operations'
                }
            ],
            Operations: [
                ...prev.Operations,
                {
                    round: 3,
                    agent: 'Operations',
                    messageType: 'vote',
                    content: 'Voted for Planner'
                }
            ],
            HumanFlourishing: [
                ...prev.HumanFlourishing,
                {
                    round: 3,
                    agent: 'HumanFlourishing',
                    messageType: 'vote',
                    content: 'Voted for Operations'
                }
            ],
            Moderator: []
        }))
        setWinner('Operations')
        setVoteTally({
            Planner: 1,
            Operations: 2,
            HumanFlourishing: 0,
            Moderator: 0
        })
    }

    return (
        <main className="min-h-screen px-6 pt-32 pb-6">
            <div className="w-full max-w-6xl mx-auto">
                <h1 className="mb-8 text-4xl font-bold text-white">
                    Debate Viewer Test
                </h1>

                <div className="flex gap-3 mb-6">
                    <Button onClick={addTestProposal}>
                        Add Proposals (Round 1)
                    </Button>
                    <Button onClick={addTestRebuttal}>
                        Add Rebuttals (Round 2)
                    </Button>
                    <Button onClick={addTestVoting}>
                        Add Voting (Round 3)
                    </Button>
                    <Button 
                        onClick={() => {
                            setMessages({
                                Planner: [],
                                Operations: [],
                                HumanFlourishing: [],
                                Moderator: []
                            })
                            setCurrentRound(1)
                            setWinner(undefined)
                            setVoteTally(undefined)
                        }}
                        variant="outline"
                    >
                        Reset
                    </Button>
                </div>

                <DebateViewer
                    messages={messages}
                    currentRound={currentRound}
                    winner={winner}
                    voteTally={voteTally}
                />
            </div>
        </main>
    )
}